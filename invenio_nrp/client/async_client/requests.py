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
from types import SimpleNamespace
from typing import Annotated, Any, Optional

from pydantic import AfterValidator, BeforeValidator, Field, fields, model_validator

from ...generic import generic_arguments
from ...types.base import Model
from ...types.yarl_url import YarlURL
from .connection import Connection
from .rest import BaseRecord, RESTList, RESTObjectLinks


def single_value_expected(value):
    assert len(value) == 1, "Expected exactly one value"


class RequestActionLinks(Model):
    """Possible actions on a request"""

    submit: Optional[YarlURL] = None
    cancel: Optional[YarlURL] = None
    accept: Optional[YarlURL] = None
    decline: Optional[YarlURL] = None


class RequestLinks(RESTObjectLinks):
    """Links on a request"""

    actions: RequestActionLinks
    """Actions that can be performed on the request at the moment by the current user."""

    self_: YarlURL = fields.Field(alias="self")
    """Link to the request itself"""

    comments: YarlURL
    """Link to the comments on the request"""

    timeline: YarlURL
    """Link to the timeline (events) of the request"""


class RequestStatus(StrEnum):
    CREATED = auto()
    ACCEPTED = auto()
    DECLINED = auto()
    SUBMITTED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


JSONRequestStatus = Annotated[
    RequestStatus,
    BeforeValidator(lambda x: RequestStatus(x) if isinstance(x, str) else x),
]


class RequestPayloadRecord(Model):
    """A publish/edit/new version request can have a simplified record serialization inside its payload.
    Currently the serialization contains only links to the published/draft record.
    """

    links: RESTObjectLinks
    """Links to the record (self and self_html)"""


class RequestPayload(Model):
    """Payload of a request. It can be of different types, depending on the request type.
    In the library, the payload is extensible. If you know that there is a specific property
    on the payload, just use payload.property_name to access it.
    """

    published_record: RequestPayloadRecord = None
    """A publish request can have a simplified record serialization inside its payload."""

    draft_record: RequestPayloadRecord = None
    """An edit request can have a simplified record serialization inside its payload."""

    @model_validator(mode="before")
    @classmethod
    def __pydantic_restore_hierarchy(cls, data: Any) -> Any:
        if not data:
            return {}
        obj = {}
        for k, v in data.items():
            cls._parse_colon_hierarchy(obj, k, v)
        return obj

    @classmethod
    def _parse_colon_hierarchy(self, obj, key, value):
        parts = key.split(":")
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        obj[parts[-1]] = value


class Request(BaseRecord):
    """Interface for a request in the NRP repository."""

    links: RequestLinks
    """Links on the request object."""

    type: str
    """Request type identifier."""

    title: Optional[str]
    """Title of the request, might be None"""

    status: JSONRequestStatus
    """Status of the request"""

    is_closed: bool
    """Is the request closed?"""

    is_open: bool
    """Is the request open?"""

    expires_at: Optional[datetime] = Field(None, strict=False)
    """When the request expires, might be unset"""

    is_expired: bool
    """Is the request expired?"""

    # TODO: maybe use special class for this with (type, id) fields and not generic dicts
    created_by: Annotated[dict[str, str], AfterValidator(single_value_expected)]
    """Who created the request. It is a dictionary containing a 
    reference to the creator (NOT the links at the moment)."""

    receiver: Annotated[dict[str, str], AfterValidator(single_value_expected)]
    """Who is the receiver of the request. It is a dictionary containing a 
    reference to the receiver (NOT the links at the moment)."""

    topic: Annotated[dict[str, str], AfterValidator(single_value_expected)]
    """The topic of the request. It is a dictionary containing a
    reference to the topic (NOT the links at the moment)."""

    payload: Optional[RequestPayload] = None
    """Payload of the request. It can be of different types, depending on the request type."""

    def submit(self, payload=None):
        """Submit the request. The request will be either passed to receivers, or auto-approved
        depending on the current workflow
        """
        return self._push_request(
            required_request_status=RequestStatus.CREATED,
            action="submit",
            payload=payload,
        )

    def accept(self, payload=None):
        """Accept the submitted request."""
        return self._push_request(
            required_request_status=RequestStatus.SUBMITTED,
            action="accept",
            payload=payload,
        )

    def decline(self, payload=None):
        """Decline the submitted request."""
        return self._push_request(
            required_request_status=RequestStatus.SUBMITTED,
            action="decline",
            payload=payload,
        )

    def cancel(self, payload=None):
        """Cancel the request."""
        return self._push_request(
            required_request_status=RequestStatus.CREATED,
            action="cancel",
            payload=payload,
        )

    def _push_request(self, *, required_request_status, action, payload):
        if self.status != required_request_status:
            raise ValueError(
                f"Can {action} only requests with status {required_request_status}, not {self.status}"
            )

        action_link = getattr(self.links.actions, action)

        if not action_link:
            raise ValueError(f"You have no permission to {action} this request")

        return self._connection.post(
            url=action_link, json=payload or {}, result_class=type(self)
        )


class RequestList[RequestBase: Request](
    RESTList[RequestBase]  # noqa (RequestBase looks like not defined in pycharm)
):
    """A list of requests."""

    sortBy: Optional[str]
    """By which property should be the list sorted"""

    aggregations: Optional[Any]
    """Aggregations of the list"""

    hits: list[RequestBase]
    """List of requests that matched the search query"""


class RequestClient[RequestBase: Request]:
    """Record requests. Usually not used directly, but through AsyncClient().requests() call"""

    def __init__(self, connection: Connection, requests_url: str):
        """Initialize the class.

        :param connection: Connection to the NRP repository
        :param requests_url: URL to the requests endpoint
        """
        self._connection = connection
        self._requests_url = requests_url

    @property
    def _generic_arguments(self) -> SimpleNamespace:
        return generic_arguments.actual_types(self)

    async def all(self, **params) -> RequestList[RequestBase]:
        """Search for all requests the user has access to.

        :param params:  Additional parameters to pass to the search query, see invenio docs for possible values
        """
        return await self._connection.get(
            url=self._requests_url,
            result_class=RequestList[self._generic_arguments.RequestBase],
            result_context={"connection": self._connection},
            params=params,
        )

    async def created(self, **params) -> RequestList[RequestBase]:
        """Return all requests, that are created but not yet submitted"""
        return await self.all(status="created", **params)

    async def submitted(self, **params) -> RequestList[RequestBase]:
        """Return all submitted requests"""
        return await self.all(status="submitted", **params)

    async def accepted(self, **params) -> RequestList[RequestBase]:
        """Return all accepted requests"""
        return await self.all(status="accepted", **params)

    async def declined(self, **params) -> RequestList[RequestBase]:
        """Return all declined requests"""
        return await self.all(status="declined", **params)

    async def expired(self, **params) -> RequestList[RequestBase]:
        """Return all expired requests"""
        return await self.all(status="expired", **params)

    async def cancelled(self, **params) -> RequestList[RequestBase]:
        """Return all cancelled requests"""
        return await self.all(status="cancelled", **params)

    async def read_request(self, request_id) -> RequestBase:
        """Read a single request by its id"""
        return await self._connection.get(
            url=f"{self._requests_url}/{request_id}",
            result_class=self._generic_arguments.RequestBase,
        )
