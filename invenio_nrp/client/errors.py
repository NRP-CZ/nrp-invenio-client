#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Errors raised from invenio repository."""

import json
from typing import Any


class RepositoryError(Exception):
    """Base class for all repository errors."""

    pass


class RepositoryCommunicationError(RepositoryError):
    """Base class for all repository communication errors."""


class RepositoryNetworkError(RepositoryCommunicationError):
    """Raised when a network error occurs."""


class RepositoryJSONError(RepositoryCommunicationError):
    """Raised from a repository when an error occurs."""

    def __init__(self, request_info: Any, response: dict):  # noqa ANN401
        """Initialize the error."""
        self._request_info = request_info
        self._response = response

    @property
    def request_info(self) -> Any:
        """Return the request info."""
        return self._request_info

    @property
    def json(self) -> dict:
        """Return the JSON response."""
        return self._response

    def __repr__(self) -> str:
        """Return the representation of the error."""
        return f"{self._request_info.url} : {json.dumps(self.json)}"

    def __str__(self) -> str:
        """Return the string representation of the error."""
        return self.__repr__()


class RepositoryServerError(RepositoryJSONError):
    """An error occurred on the server side (5xx http status code)."""


class RepositoryClientError(RepositoryJSONError):
    """An error occurred on the client side (4xx http status code).

    This is usually not found, unauthorized, malformed request and similar.
    """
