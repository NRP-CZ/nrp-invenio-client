#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Representation of invenio files."""

from enum import StrEnum
from pathlib import Path
from typing import Any, Optional, Self

from attrs import define, field
from yarl import URL

from ....converter import Rename, extend_serialization
from ....types import Model
from ..connection import Connection
from ..rest import RESTObject, RESTObjectLinks
from .source import DataSource


class TransferType(StrEnum):
    """Transfer types between local/remote storage and repository."""

    LOCAL = "L"
    MULTIPART = "M"
    FETCH = "F"
    REMOTE = "R"


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
        file: DataSource | str | Path,
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
        if isinstance(file, (str, Path)):
            from .source.file import FileDataSource

            file = FileDataSource(file)

        # 1. initialize the upload
        transfer_md: dict[str, Any] = {}
        transfer_payload = {"key": key, "metadata": metadata, "transfer": transfer_md}
        if transfer_type != TransferType.LOCAL:
            transfer_md["type"] = transfer_type

        if transfer_metadata:
            transfer_md.update(transfer_metadata)

        from .transfer import transfer_registry

        transfer = transfer_registry.get(transfer_type)

        await transfer.prepare(self._connection, 
                               self._files_endpoint, 
                               transfer_payload, 
                               file)

        initialized_upload: FilesList = await self._connection.post(
            url=self._files_endpoint,
            json=[transfer_payload],
            result_class=FilesList,
        )

        initialized_upload_metadata = initialized_upload[key]

        # 2. upload the file using one of the transfer types
        await transfer.upload(self._connection, initialized_upload_metadata, file)

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
