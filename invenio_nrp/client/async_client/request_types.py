#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Types of requests that the user can apply for."""

from typing import Optional

from attrs import define
from yarl import URL

from ...types import Model
from .requests import Request
from .rest import RESTList, RESTObject


@define(kw_only=True)
class RequestTypeActionLinks(Model):
    """Links on a request type object."""

    create: Optional[URL] = None
    """Link to create a new request of this type."""


@define(kw_only=True)
class RequestTypeLinks(Model):
    """Links on a request type."""

    actions: RequestTypeActionLinks
    """Actions that can be performed on the request type."""


@define(kw_only=True)
class RequestType(RESTObject):
    """A type of request that the user can apply for.

    An example might be a request for access to a dataset,
    publish draft request, assign doi request, ...
    """

    type_id: str
    """Unique identifier of the request type."""

    links: RequestTypeLinks
    """Links on the request type object."""

    async def create(self, payload: dict, submit: bool = False) -> Request:
        """Create a new request of this type."""
        request: Request = await self._connection.post(
            url=self.links.actions.create,
            json=payload,
            result_class=Request,
        )
        if submit:
            return await request.submit()
        return request


@define(kw_only=True)
class RequestTypeList(RESTList[RequestType]):
    """A list of request types as returned from the API."""

    def __getitem__(self, type_id: str) -> RequestType:
        """Return a request type by its type_id.

        :param type_id:     type_id, stays stable regardless of server version
        :return:            request type or None if not found
        """
        for hit in self.hits:
            if hit.type_id == type_id:
                return hit
        raise KeyError(f"Request type {type_id} not found")

    def keys(self) -> set[str]:
        """Return all type_ids of the request types in this list.

        :return: a set of type_ids
        """
        return {hit.type_id for hit in self.hits}

    def __getattr__(self, type_id: str) -> RequestType:
        """Return a request type by its type_id.

        Shortcut to be able to write request_types.publish_draft instead of request_types["publish_draft"]
        """
        if type_id in self.keys():
            return self[type_id]
        return super().__getattr__(type_id)
