#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import json
from typing import Any, Dict


class RepositoryError(Exception):
    pass


class RepositoryCommunicationError(RepositoryError):
    """
    Base class for all repository communication errors.
    """


class RepositoryNetworkError(RepositoryCommunicationError):
    """
    Raised when a network error occurs.
    """


class RepositoryJSONError(RepositoryCommunicationError):
    def __init__(self, request_info: Any, response: Dict):
        self._request_info = request_info
        self._response = response

    @property
    def json(self):
        return self._response

    def __repr__(self):
        return f"{self._request_info.url} : {json.dumps(self.json)}"

    def __str__(self):
        return self.__repr__()


class RepositoryServerError(RepositoryJSONError):
    """An error occurred on the server side (5xx http status code)."""


class RepositoryClientError(RepositoryJSONError):
    """An error occurred on the client side (4xx http status code),
    usually not found, unauthorized, malformed request, ..."""
