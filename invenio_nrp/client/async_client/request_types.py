#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Types of requests that the user can apply for."""
from types import SimpleNamespace
from typing import List, Optional

from ...generic import generic_arguments
from ...types import Model, YarlURL
from .requests import Request
from .rest import RESTList, RESTObject


class RequestTypeActionLinks(Model):
    """Links on a request type object."""

    create: Optional[YarlURL] = None
    """Link to create a new request of this type."""


class RequestTypeLinks(Model):
    """Links on a request type"""

    actions: RequestTypeActionLinks
    """Actions that can be performed on the request type."""


class RequestType[RequestBase: Request](RESTObject):
    """
    A type of request that the user can apply for. An example might be a request for access to a dataset,
    publish draft request, assign doi request, ...
    """

    type_id: str
    """Unique identifier of the request type."""

    links: RequestTypeLinks
    """Links on the request type object."""

    @property
    def _generic_arguments(self) -> SimpleNamespace:
        return generic_arguments.actual_types(self)

    async def create(self, payload, submit=False) -> RequestBase:
        """
        Create a new request of this type.
        """
        request: RequestBase = await self._connection.post(
            url=self.links.actions.create,
            json=payload,
            result_class=self._generic_arguments.RequestBase,
        )
        if submit:
            return await request.submit()
        return request


class RequestTypeList[RequestTypeBase: RequestType[Request]](
    RESTList[
        RequestTypeBase
    ]  # noqa (RequestTypeBase looks like not defined in pycharm)
):
    """A list of request types as returned from the API"""

    hits: List[RequestTypeBase]
    """Internal list of request types"""

    def __getitem__(self, type_id) -> RequestTypeBase:
        """
        Returns a request type by its type_id

        :param type_id:     type_id, stays stable regardless of server version
        :return:            request type or None if not found
        """
        for hit in self.hits:
            if hit.type_id == type_id:
                return hit

    def keys(self):
        """
        Return all type_ids of the request types in this list.

        :return: a set of type_ids
        """
        return {hit.type_id for hit in self.hits}

    def __getattr__(self, item):
        """Shortcut to be able to write request_types.publish_draft instead of request_types["publish_draft"]"""
        if item in self.keys():
            return self[item]
        return super().__getattr__(item)