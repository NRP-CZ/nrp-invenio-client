#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of the client for requests inside the NRP repository."""

from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Optional, Self

from attrs import define
from cattrs.dispatch import StructureHook
from yarl import URL

from ...types.base import Model
from ...types.converter import Rename, WrapStructure, extend_serialization
from .connection import Connection
from .rest import BaseRecord, RESTList, RESTObjectLinks


def single_value_expected(value: list[Any] | tuple[Any, ...] | dict[Any, Any]) -> None:
    """Check that the value is a single value."""
    assert len(value) == 1, "Expected exactly one value"


@define(kw_only=True)
class RequestActionLinks(Model):
    """Possible actions on a request."""

    submit: Optional[URL] = None
    cancel: Optional[URL] = None
    accept: Optional[URL] = None
    decline: Optional[URL] = None


@extend_serialization(Rename("self", "self_"), allow_extra_data=True)
@define(kw_only=True)
class RequestLinks(RESTObjectLinks):
    """Links on a request."""

    actions: RequestActionLinks
    """Actions that can be performed on the request at the moment by the current user."""

    self_: URL
    """Link to the request itself"""

    comments: URL
    """Link to the comments on the request"""

    timeline: URL
    """Link to the timeline (events) of the request"""


class RequestStatus(StrEnum):
    """Status of the request."""

    CREATED = auto()
    ACCEPTED = auto()
    DECLINED = auto()
    SUBMITTED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


@define(kw_only=True)
class RequestPayloadRecord(Model):
    """A publish/edit/new version request can have a simplified record serialization inside its payload.

    Currently the serialization contains only links to the published/draft record.
    """

    links: RESTObjectLinks
    """Links to the record (self and self_html)"""


def restore_hierarchy(data: dict[str, Any], type_: type, previous: StructureHook) -> Any:
    """Restore the hierarchy of the request payload."""

    def _parse_colon_hierarchy(obj: dict[str, Any], key: str, value: Any) -> None:
        parts = key.split(":")
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        obj[parts[-1]] = value

    if not data:
        return previous(data, type_)
    
    obj: dict[str, Any] = {}
    for k, v in data.items():
        _parse_colon_hierarchy(obj, k, v)
    return previous(obj, type_)

@extend_serialization(WrapStructure(restore_hierarchy), allow_extra_data=False)
@define(kw_only=True)
class RequestPayload(Model):
    """Payload of a request.

    It can be of different types, depending on the request type.
    In the library, the payload is extensible. If you know that there is a specific property
    on the payload, just use payload.property_name to access it.
    """

    published_record: RequestPayloadRecord | None = None
    """A publish request can have a simplified record serialization inside its payload."""

    draft_record: RequestPayloadRecord | None = None
    """An edit request can have a simplified record serialization inside its payload."""


@define(kw_only=True)
class Request(BaseRecord):
    """Interface for a request in the NRP repository."""

    links: RequestLinks
    """Links on the request object."""

    type: str
    """Request type identifier."""

    title: Optional[str] = None
    """Title of the request, might be None"""

    status: RequestStatus
    """Status of the request"""

    is_closed: bool
    """Is the request closed?"""

    is_open: bool
    """Is the request open?"""

    expires_at: Optional[datetime] = None
    """When the request expires, might be unset"""

    is_expired: bool
    """Is the request expired?"""

    created_by: dict[str, str]
    """Who created the request. It is a dictionary containing a 
    reference to the creator (NOT the links at the moment)."""

    receiver: dict[str, str]
    """Who is the receiver of the request. It is a dictionary containing a 
    reference to the receiver (NOT the links at the moment)."""

    topic: dict[str, str]
    """The topic of the request. It is a dictionary containing a
    reference to the topic (NOT the links at the moment)."""

    payload: Optional[RequestPayload] = None
    """Payload of the request. It can be of different types, depending on the request type."""

    def __attrs_post_init__(self):
        """Check that the created_by, receiver and topic are single values."""
        single_value_expected(self.created_by)
        single_value_expected(self.receiver)
        single_value_expected(self.topic)

    async def submit(self, payload: dict | None = None) -> Self:
        """Submit the request.

        The request will be either passed to receivers, or auto-approved
        depending on the current workflow
        """
        return await self._push_request(
            required_request_status=RequestStatus.CREATED,
            action="submit",
            payload=payload,
        )

    async def accept(self, payload: dict | None = None) -> Self:
        """Accept the submitted request."""
        return await self._push_request(
            required_request_status=RequestStatus.SUBMITTED,
            action="accept",
            payload=payload,
        )

    async def decline(self, payload: dict | None = None) -> Self:
        """Decline the submitted request."""
        return await self._push_request(
            required_request_status=RequestStatus.SUBMITTED,
            action="decline",
            payload=payload,
        )

    async def cancel(self, payload: dict | None = None) -> Self:
        """Cancel the request."""
        return await self._push_request(
            required_request_status=RequestStatus.CREATED,
            action="cancel",
            payload=payload,
        )

    async def _push_request(
        self, *, required_request_status: str, action: str, payload: dict | None
    ) -> Self:
        """Push the request to the server."""
        if self.status != required_request_status:
            raise ValueError(
                f"Can {action} only requests with status {required_request_status}, not {self.status}"
            )

        action_link = getattr(self.links.actions, action)

        if not action_link:
            raise ValueError(f"You have no permission to {action} this request")

        return await self._connection.post(
            url=action_link, json=payload or {}, result_class=type(self)
        )


@extend_serialization(allow_extra_data=False)
@define(kw_only=True)
class RequestList(RESTList[Request]):
    """A list of requests."""

    sortBy: Optional[str] = None
    """By which property should be the list sorted"""

    aggregations: Optional[Any] = None
    """Aggregations of the list"""


class RequestClient:
    """Record requests.

    Usually not used directly, but through AsyncClient().requests() call
    """

    def __init__(self, connection: Connection, requests_url: URL):
        """Initialize the class.

        :param connection: Connection to the NRP repository
        :param requests_url: URL to the requests endpoint
        """
        self._connection = connection
        self._requests_url = requests_url

    async def all(self, **params: str) -> RequestList:
        """Search for all requests the user has access to.

        :param params:  Additional parameters to pass to the search query, see invenio docs for possible values
        """
        return await self._connection.get(
            url=self._requests_url,
            result_class=RequestList,
            result_context={"connection": self._connection},
            params=params,
        )

    async def created(self, **params: str) -> RequestList:
        """Return all requests, that are created but not yet submitted."""
        return await self.all(status="created", **params)

    async def submitted(self, **params: str) -> RequestList:
        """Return all submitted requests."""
        return await self.all(status="submitted", **params)

    async def accepted(self, **params: str) -> RequestList:
        """Return all accepted requests."""
        return await self.all(status="accepted", **params)

    async def declined(self, **params: str) -> RequestList:
        """Return all declined requests."""
        return await self.all(status="declined", **params)

    async def expired(self, **params: str) -> RequestList:
        """Return all expired requests."""
        return await self.all(status="expired", **params)

    async def cancelled(self, **params: str) -> RequestList:
        """Return all cancelled requests."""
        return await self.all(status="cancelled", **params)

    async def read_request(self, request_id: str) -> Request:
        """Read a single request by its id."""
        return await self._connection.get(
            url=self._requests_url / request_id,
            result_class=Request,
        )
