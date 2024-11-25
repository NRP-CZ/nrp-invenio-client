#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Record client."""

import copy
from typing import Any, Dict, Optional, Protocol, Self

from pydantic import field_validator, fields
from yarl import URL

from ...types import Model, YarlURL
from .connection import Connection
from .files import FilesClient
from .record_requests import RecordRequestsClient
from .rest import BaseRecord, RESTList, RESTObjectLinks


class RecordLinks(RESTObjectLinks):
    """Links of a record."""

    # TODO: add rest of the links here so that code editors can autocomplete
    pass


class FilesEnabled(Model):
    """Files enabled marker."""

    enabled: bool


class Record(BaseRecord):
    """Record in the repository."""

    links: RecordLinks
    """Links of the record."""
    metadata: Optional[dict[str, Any]] = None
    """Metadata of the record."""
    files_: Optional[FilesEnabled] = fields.Field(alias="files")
    """Files enabled marker."""

    @field_validator("files_", mode="before")
    @classmethod
    def transform(cls, raw: Any) -> Dict:  # noqa: ANN401
        """Transform the raw data, zenodo serialization."""
        if isinstance(raw, list):
            # zenodo serialization
            return {"enabled": len(raw) > 0}
        return raw

    async def delete(self) -> None:
        """Delete the record."""
        return await self._connection.delete(
            url=self.links.self_, headers=self._etag_headers()
        )

    async def update(self, force_etag: bool = False) -> Self:
        """Update the record."""
        headers = {}
        if not force_etag:
            headers.update(self._etag_headers())

        ret = await self._connection.put(
            url=self.links.self_,
            data=self.model_dump_json(),  # type: ignore
            headers={
                **headers,
                "Content-Type": "application/json",
            },
            result_class=type(self),
        )
        return ret

    def requests(
        self,
    ) -> RecordRequestsClient:
        """Get the requests client for the record."""
        return RecordRequestsClient(
            self._connection, self.links.requests, self.links.applicable_requests
        )

    def files(self) -> FilesClient:
        """Get the files client for the record."""
        return FilesClient(self._connection, self.links.files)


class RecordList(RESTList[Record]):
    """List of records."""

    sortBy: Optional[str]
    """Sort by field."""
    aggregations: Optional[Any]
    """Aggregations."""
    hits: list[Record]
    """List of records."""


class CreateURL(Protocol):
    """Callable that returns the URL for creating a record."""

    def __call__(self) -> YarlURL: ...  # noqa


class ReadURL(Protocol):
    """Callable that returns the URL for reading a record."""

    def __call__(self, record_id: str) -> YarlURL: ...  # noqa


class SearchURL(Protocol):
    """Callable that returns the URL for searching records."""

    def __call__(self) -> YarlURL: ...  # noqa


class RecordClient:
    """Client for records in the repository."""

    def __init__(
        self,
        connection: Connection,
        create_url: CreateURL,
        read_url: ReadURL,
        search_url: SearchURL,
    ):
        """Initialize the client."""
        self._connection = connection
        self._create_url = create_url
        self._read_url = read_url
        self._search_url = search_url

    async def create_record(
        self,
        data: dict,
        community: str | None = None,
        workflow: str | None = None,
        idempotent: bool = False,
        files_enabled: bool = True,
    ) -> Record:
        """Create a new record in the repository.

        :param data:            the metadata of the record
        :param community:       community in which the record should be created
        :param workflow:        the workflow to use for the record, if not provided
                                the default workflow of the community is used
        :param idempotent:      if True, the operation is idempotent and can be retried on network errors.
                                Use only if you know that the operation is idempotent, for example that
                                you use PID generator that takes the persistent identifier from the data.
        :return:                the created record
        """
        if idempotent:
            raise NotImplementedError("Idempotent for create not implemented yet")

        create_url: YarlURL = self._create_url()

        data = {**data}
        if community or workflow:
            parent = copy.deepcopy(data.pop("parent")) if "parent" in data else {}
            data["parent"] = parent
            if community:
                assert (
                    "community" not in parent
                ), f"Community already in parent: {parent}"
                parent["communities"] = {"default": community}
            if workflow:
                assert "workflow" not in parent, f"Workflow already in data: {parent}"
                parent["workflow"] = workflow
        data["files"] = {"enabled": files_enabled}

        return await self._connection.post(
            url=create_url,
            json=data,
            idempotent=idempotent,
            result_class=Record,
        )

    async def read_record(
        self,
        *,
        record_id: str,
        expand: bool = False,
    ) -> Record:
        """Read a record from the repository. Please provide either record_id or record_url, not both.

        :param record_id:       the id of the record. Could be either pid or url
        :return:                the record
        """
        record_url = self._read_url(record_id)

        if expand:
            record_url = str(URL(record_url).with_query(expand="true"))
        return await self._connection.get(
            url=record_url,
            result_class=Record,
        )

    async def search(
        self,
        *,
        q: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        **facets: str,
    ) -> RecordList:
        """Search for records in the repository."""
        search_url: YarlURL = self._search_url()
        query = {**facets}
        if q:
            query["q"] = q
        if page is not None:
            query["page"] = str(page)
        if size is not None:
            query["size"] = str(size)

        return await self._connection.get(
            url=search_url,
            params=query,
            result_class=RecordList,
        )
