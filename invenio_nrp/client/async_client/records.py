#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import copy
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Protocol, Self

from pydantic import field_validator, fields
from yarl import URL

from ...generic import generic_arguments
from ...types import Model, YarlURL
from .connection import Connection
from .files import File, FilesClient
from .record_requests import RecordRequestsClient
from .request_types import RequestType
from .requests import Request
from .rest import BaseRecord, RESTList, RESTObjectLinks


class RecordLinks(RESTObjectLinks):
    # TODO: add rest of the links here so that code editors can autocomplete
    pass


class FilesEnabled(Model):
    enabled: bool


class Record[
    FileBase: File, RequestBase: Request, RequestTypeBase: RequestType[Request]
](BaseRecord):

    links: RecordLinks
    metadata: Optional[Dict[str, Any]] = None
    files_: Optional[FilesEnabled] = fields.Field(alias="files")

    @field_validator("files_", mode="before")
    @classmethod
    def transform(cls, raw: any) -> Dict:
        if isinstance(raw, list):
            # zenodo serialization
            return {"enabled": len(raw) > 0}
        return raw

    @property
    def _generic_arguments(self) -> SimpleNamespace:
        return generic_arguments.actual_types(self)

    async def delete(self):
        return await self._connection.delete(
            url=self.links.self_, headers=self._etag_headers()
        )

    async def update(self, force_etag=False) -> Self:
        headers = {}
        if not force_etag:
            headers.update(self._etag_headers())

        ret = await self._connection.put(
            url=self.links.self_,
            data=self.model_dump_json(),
            headers={
                **headers,
                "Content-Type": "application/json",
            },
            result_class=type(self),
        )
        return ret

    def requests(
        self,
    ) -> RecordRequestsClient[RequestBase, RequestTypeBase]:
        return RecordRequestsClient[
            self._generic_arguments.RequestBase,
            self._generic_arguments.RequestTypeBase,
        ](self._connection, self.links.requests, self.links.applicable_requests)

    def files(self) -> FilesClient[FileBase]:
        return FilesClient[self._generic_arguments.FileBase](
            self._connection, self.links.files
        )


class RecordList[RecordBase](
    RESTList[RecordBase]
):  # noqa (RequestBase looks like not defined in pycharm)
    sortBy: Optional[str]
    aggregations: Optional[Any]
    hits: List[RecordBase]


class CreateURL(Protocol):
    def __call__(self) -> YarlURL: ...


class ReadURL(Protocol):
    def __call__(self, record_id: str) -> YarlURL: ...


class SearchURL(Protocol):
    def __call__(self) -> YarlURL: ...


class RecordClient[RecordBase: Record]:
    def __init__(
        self,
        connection: Connection,
        model: str,
        create_url: CreateURL,
        read_url: ReadURL,
        search_url: SearchURL,
    ):
        self._connection = connection
        self._model = model
        self._create_url = create_url
        self._read_url = read_url
        self._search_url = search_url

    @property
    def _generic_arguments(self) -> SimpleNamespace:
        return generic_arguments.actual_types(self)

    async def create_record(
        self,
        data: dict,
        community: str = None,
        workflow: str = None,
        idempotent: bool = False,
        files_enabled: bool = True,
    ) -> RecordBase:
        """
        Create a new record in the repository.

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
            if "parent" in data:
                parent = copy.deepcopy(data.pop("parent"))
            else:
                parent = {}
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
            result_class=self._generic_arguments.RecordBase,
        )

    async def read_record(
        self,
        *,
        record_id: Optional[str] = None,
        expand=False,
    ) -> RecordBase:
        """
        Read a record from the repository. Please provide either record_id or record_url, not both.

        :param record_id:       the id of the record. Could be either pid or url
        :return:                the record
        """
        record_url = self._read_url(record_id)

        if expand:
            record_url = str(URL(record_url).with_query(expand="true"))
        return await self._connection.get(
            url=record_url,
            result_class=self._generic_arguments.RecordBase,
        )

    async def search(
        self,
        *,
        q: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        **facets,
    ) -> RecordList[RecordBase]:

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
            result_class=RecordList[self._generic_arguments.RecordBase],
        )
