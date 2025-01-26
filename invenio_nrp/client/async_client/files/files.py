#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Representation of invenio files."""

import asyncio
from pathlib import Path
from typing import Any, Optional, Self

from attrs import define, field
from yarl import URL

from ....converter import Rename, extend_serialization
from ....types import Model
from ...errors import RepositoryClientError
from ..connection import Connection
from ..rest import RESTObject, RESTObjectLinks
from ..streams import DataSink, DataSource
from .transfer import TransferType
from .transfer.aws_limits import (
    MINIMAL_DOWNLOAD_PART_SIZE,
    adjust_download_multipart_params,
)


@extend_serialization(Rename("type", "type_"), allow_extra_data=True)
@define(kw_only=True)
class FileTransfer(Model):
    """File transfer metadata."""

    type_: str = field(default=TransferType.LOCAL.value)


@define(kw_only=True)
class MultipartUploadLinks(Model):
    """Links for multipart uploads."""

    url: URL
    """The url where to upload the part to."""


@extend_serialization(Rename("self", "self_"), allow_extra_data=True)
@define(kw_only=True)
class FileLinks(RESTObjectLinks):
    """Links for a single invenio file."""

    content: Optional[URL] = None
    """Link to the content of the file."""

    commit: Optional[URL] = None
    """Link to commit (finalize) uploading of the file."""

    parts: Optional[list[MultipartUploadLinks]] = None
    """For multipart upload, links where to upload the part to."""


@extend_serialization(allow_extra_data=True)
@define(kw_only=True)
class File(RESTObject):
    """A file object as stored in .../files/<key>."""

    key: str
    """Key(filename) of the file."""

    metadata: dict[str, Any] = field(factory=dict)
    """Metadata of the file, as defined in the model."""

    links: FileLinks
    """Links to the file content and commit."""

    transfer: FileTransfer = field(
        factory=lambda: FileTransfer(type_=TransferType.LOCAL.value)
    )
    """File transfer type and metadata."""

    status: Optional[str] = None

    async def save(self) -> Self:
        """Save the file metadata."""
        return await self._connection.put(
            url=self.links.self_,
            json={
                "metadata": self.metadata,
            },
            result_class=type(self),
        )

    async def download(self, sink: DataSink, 
                       parts: int | None = None,
                       part_size: int | None = None) -> None:
        """Download the file content to a sink.

        Will use
        :param sink: The sink to download the file to.
        """
        if self.links.content is None:
            raise ValueError("No content link available for the file")

        try:
            headers = await self._connection.head(url=self.links.content)
        except RepositoryClientError:
            # The file is not available for HEAD. This is the case for S3 files
            # where the file is a pre-signed request. We'll try to download the headers
            # with a GET request with a range header containing only the first byte.
            headers = await self._connection.head(url=self.links.content, use_get=True)

        size = 0
        location = URL(headers.get('Location', self.links.content))
        
        if "Content-Length" in headers:
            size = int(headers["Content-Length"])
            await sink.allocate(size)

        if (
            size
            and size > MINIMAL_DOWNLOAD_PART_SIZE
            and any(x == "bytes" for x in headers.getall("Accept-Ranges"))
        ):
            await self._download_multipart(location, sink, size, parts, part_size)
        else:
            await self._download_single(location, sink)

    async def _download_single(self, url: URL, sink: DataSink) -> None:
        await self._connection.get_stream(url=url, sink=sink, offset=0)

    async def _download_multipart(
        self, url: URL, sink: DataSink, size: int, parts: int | None = None, part_size: int | None = None
    ) -> None:
        adjusted_parts, adjusted_part_size = adjust_download_multipart_params(size, parts, part_size)

        async with asyncio.TaskGroup() as tg:
            for i in range(adjusted_parts):
                start = i * adjusted_part_size
                size = min((i + 1) * adjusted_part_size, size) - start
                tg.create_task(
                    self._connection.get_stream(
                        url=url, sink=sink, offset=start, size=size
                    )

                )


@define(kw_only=True)
class FilesList(RESTObject):
    """A list of files, as stored in ...<record_id>/files."""

    enabled: bool
    """Whether the files are enabled on the record."""

    entries: list[File] = field(factory=list)
    """List of files on the record."""

    def __getitem__(self, key: str) -> File:
        """Get a file by key."""
        for v in self.entries:
            if v.key == key:
                return v
        raise KeyError(f"File with key {key} not found")


class FilesClient:
    """Client for the files endpoint.

    Normally not used directly but from AsyncClient().records.read(...).files.
    """

    def __init__(self, connection: Connection, files_endpoint: URL):
        """Initialize the client.

        :param connection: Connection to the repository
        :param files_endpoint: The files endpoint
        """
        self._connection = connection
        self._files_endpoint = files_endpoint

    async def list(self) -> FilesList:
        """List all files on the record and their upload status."""
        return await self._connection.get(
            url=self._files_endpoint,
            result_class=FilesList,
        )

    async def upload(
        self,
        key: str,
        metadata: dict[str, Any],
        source: DataSource | str | Path,
        transfer_type: TransferType = TransferType.LOCAL,
        transfer_metadata: dict | None = None,
    ) -> File:
        """Upload a file to the repository.

        :param key:                 the key (filename) of the file
        :param metadata:            metadata of the file, as defined in the model inside the repository
        :param file:                the file to upload. Can be either an initialized data source or path on the filesystem
        :param transfer_type:       type of the transfer to use, currently supported is the LOCAL transfer type
        :param transfer_metadata:   extra metadata for the transfer
        :return:                    metadata of the uploaded file
        """
        if isinstance(source, str | Path):
            from .source.file import FileDataSource

            source = FileDataSource(source)

        # 1. initialize the upload
        transfer_md: dict[str, Any] = {}
        transfer_payload = {"key": key, "metadata": metadata, "transfer": transfer_md}
        if transfer_type != TransferType.LOCAL:
            transfer_md["type"] = transfer_type

        if transfer_metadata:
            transfer_md.update(transfer_metadata)

        from .transfer import transfer_registry

        transfer = transfer_registry.get(transfer_type)

        await transfer.prepare(
            self._connection, self._files_endpoint, transfer_payload, source
        )

        initialized_upload: FilesList = await self._connection.post(
            url=self._files_endpoint,
            json=[transfer_payload],
            result_class=FilesList,
        )

        initialized_upload_metadata = initialized_upload[key]

        # 2. upload the file using one of the transfer types
        await transfer.upload(self._connection, initialized_upload_metadata, source)

        # 3. prepare the commit payload
        commit_payload = await transfer.get_commit_payload(initialized_upload_metadata)

        if initialized_upload_metadata.links.commit:
            committed_upload = await self._connection.post(
                url=initialized_upload_metadata.links.commit,
                json=commit_payload,
                result_class=File,
            )

            return committed_upload
        else:
            return initialized_upload_metadata
