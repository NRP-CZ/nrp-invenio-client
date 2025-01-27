#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base rest types."""

from datetime import datetime
from types import UnionType
from typing import (
    Any,
    AsyncGenerator,
    Iterator,
    Optional,
    Self,
    Union,
    get_args,
    get_origin,
)

from attrs import define, field
from yarl import URL

from ...converter import Rename, converter, extend_serialization
from ...types import Model
from .connection import Connection, ConnectionMixin


@extend_serialization(Rename("self", "self_"), allow_extra_data=True)
@define(kw_only=True)
class RESTObjectLinks(Model):
    """Each rest object must return a links section."""

    self_: URL
    """Link to the object itself (API)"""

    self_html: Optional[URL] = None
    """Link to the object itself (HTML page if it has any)"""


@define(kw_only=True)
class RESTObject(ConnectionMixin, Model):
    """Base class for all objects returned from the REST API."""

    links: RESTObjectLinks
    """Links to the object itself"""


@extend_serialization(Rename("self", "self_"), allow_extra_data=True)
@define(kw_only=True)
class RESTPaginationLinks(Model):
    """Extra links on the pagination response."""

    self_: URL
    """Link to the current page"""

    next: Optional[URL] = None
    """Link to the next page"""

    prev: Optional[URL] = None
    """Link to the previous page"""


@define(kw_only=True)
class RESTHits[T: RESTObject](Model):
    """List of records on the current page."""

    hits: list[T]
    """List of records"""
    
    total: int    


    def __len__(self) -> int:
        """Return the number of records on the current page."""
        return len(self.hits)

    def __iter__(self) -> Iterator[T]:
        """Iterate over the records on the current page."""
        return iter(self.hits)
    
    def __getitem__(self, index: int) -> T:
        """Return the record at the given index."""
        return self.hits[index]


@define(kw_only=True)
class RESTList[T: RESTObject](RESTObject):
    """List of REST objects according to the Invenio REST API conventions."""

    links: RESTPaginationLinks
    """Links to the current page, next and previous pages"""

    hits: RESTHits[T] = field(alias='hits')
    """List of records on the current page"""

    @property
    def total(self) -> int:
        """Return the total number of records."""
        return self.hits.total

    def __len__(self) -> int:
        """Return the number of records on the current page."""
        return len(self.hits)

    def __iter__(self) -> Iterator[T]:
        """Iterate over the records on the current page."""
        return iter(self.hits)

    def has_next(self) -> bool:
        """Check if there is a next page."""
        return bool(self.links.next)

    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return bool(self.links.prev)

    async def next_page(self) -> Self:
        """Fetch and return the next page."""
        if self.links.next:
            return await self._connection.get(
                url=self.links.next,
                result_class=type(self),
            )
        raise StopIteration()

    async def prev_page(self) -> Self:
        """Fetch and return the previous page."""
        if self.links.prev:
            return await self._connection.get(
                url=self.links.prev,
                result_class=type(self),
            )
        raise StopIteration()

    async def all(self) -> AsyncGenerator[T, None]:
        """Iterate over all records in all pages, starting from the current page."""
        page = self
        for rec in page.hits:
            yield rec

        while page.has_next():
            page = await page.next_page()
            for rec in page.hits:
                yield rec

    def _set_connection_params(self, connection: Connection, etag: Optional[str] = None) -> None:
        super()._set_connection_params(connection, etag)
        for hit in self.hits:
            hit._set_connection_params(connection, None)


@define(kw_only=True)
class BaseRecord(RESTObject):
    """Interface for a record in the NRP repository."""

    id: str | int
    """Identifier of the record"""

    created: datetime
    """Timestamp when the record was created"""

    updated: datetime
    """Timestamp when the record was last updated"""

    revision_id: Optional[int] = None
    """Internal revision identifier of the record"""


def is_record_id(t: Any) -> bool:
    """Return true if given type is record id."""
    origin = get_origin(t)
    if origin not in (UnionType, Union):
        return False
    base_types = get_args(t)
    return set(base_types) == {str, int}


converter.register_structure_hook_func(is_record_id, lambda v, ty: v)
converter.register_unstructure_hook_func(is_record_id, lambda v: v)
