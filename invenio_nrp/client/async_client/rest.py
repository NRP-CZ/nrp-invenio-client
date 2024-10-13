#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base rest types"""

from typing import Iterable, Optional, Self, Iterator, AsyncGenerator

from pydantic import Field, PrivateAttr, fields, model_validator
from pydantic_core.core_schema import ValidationInfo

from ...types import JSONDateTime
from ...types.base import Model
from ...types.yarl_url import YarlURL
from .connection import Connection


class RESTObjectLinks(Model):
    """Each rest object must return a links section"""

    self_: YarlURL = fields.Field(alias="self")
    """Link to the object itself (API)"""

    self_html: Optional[YarlURL] = None
    """Link to the object itself (HTML page if it has any)"""


class RESTObject(Model):
    """Base class for all objects returned from the REST API."""

    _connection: Connection = PrivateAttr(None)
    """Connection is automatically injected"""

    _etag: str = PrivateAttr(None)
    """etag is automatically injected if it was returned by the repository"""

    links: RESTObjectLinks
    """Links to the object itself"""

    @model_validator(mode="after")
    def __pydantic_set_connection(self, info: ValidationInfo) -> Self:
        context = info.context
        if context:
            self._connection = context.get("connection")
            self._etag = context.get("etag")
        return self

    def _etag_headers(self):
        headers = {}
        if self._etag:
            headers["If-Match"] = self._etag
        return headers


class RESTPaginationLinks(Model):
    """Extra links on the pagination response"""

    next: Optional[YarlURL] = None
    """Link to the next page"""

    self_: YarlURL = fields.Field(alias="self")
    """Link to the current page"""

    prev: Optional[YarlURL] = None
    """Link to the previous page"""


class RESTList[T:RESTObject](RESTObject):
    """List of REST objects according to the Invenio REST API conventions."""

    _connection: Connection
    """Connection to the api with get/put/post/delete operations, with the correct typing."""

    links: RESTPaginationLinks
    """Links to the current page, next and previous pages"""

    total: int
    """Total number of records that matched the search (not the number of returned records on the page)"""

    hits: list[T]
    """List of records on the current page"""

    class Config:
        extra = "forbid"

    @model_validator(mode="before")
    @classmethod
    def __pydantic_flatten_hits(cls, data: dict) -> dict:
        obj = {**data}
        hits = obj.pop("hits", {})
        obj["total"] = hits.get("total")
        obj["hits"] = hits.get("hits")
        return obj

    def __len__(self):
        """Return the number of records on the current page"""
        return len(self.hits)

    def __iter__(self) -> Iterator[T]:
        """Iterate over the records on the current page"""
        return iter(self.hits)

    def has_next(self):
        """Check if there is a next page"""
        return bool(self.links.next)

    def has_prev(self):
        """Check if there is a previous page"""
        return bool(self.links.prev)

    async def next_page(self) -> Self:
        """Fetch and return the next page"""
        if self.links.next:
            return await self._connection.get(
                url=self.links.next,
                result_class=type(self),
            )
        raise StopIteration()

    async def prev_page(self) -> Self:
        """Fetch and return the previous page"""
        if self.links.prev:
            return await self._connection.get(
                url=self.links.prev,
                result_class=type(self),
            )
        raise StopIteration()

    async def all(self) -> AsyncGenerator[T]:
        """Iterate over all records in all pages, starting from the current page."""
        page = self
        for rec in page.hits:
            yield rec

        while page.has_next():
            page = await page.next_page()
            for rec in page.hits:
                yield rec


class BaseRecord(RESTObject):
    """Interface for a record in the NRP repository."""

    id: str | int
    """Identifier of the record"""

    created: JSONDateTime = Field(strict=False)
    """Timestamp when the record was created"""

    updated: JSONDateTime = Field(strict=False)
    """Timestamp when the record was last updated"""

    revision_id: Optional[int] = None
    """Internal revision identifier of the record"""
