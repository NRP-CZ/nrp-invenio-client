#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of the client for requests inside the NRP repository."""

from types import SimpleNamespace

from yarl import URL

from .connection import Connection
from .request_types import RequestType, RequestTypeList
from .requests import RequestClient
from .rest import BaseRecord


class RecordRequestsClient(
    RequestClient
):
    def __init__(self, connection: Connection, requests_url: URL, request_types_url: URL):
        """Initialize the client. Normally not used directly,
        use AsyncClient().user_records().read(...).requests instead.

        :param connection:              connection to the NRP repository
        :param requests_url:            URL of the requests endpoint for the record
        :param request_types_url:       URL of the request types endpoint for the record
        """
        super().__init__(connection, requests_url)
        self._request_types_url = request_types_url

    async def applicable(self, **params) -> RequestTypeList:
        """Return all applicable requests (that is those that the current user can apply for)."""
        return await self._connection.get(
            url=self._request_types_url,
            result_class=RequestTypeList,
            params=params,
        )
