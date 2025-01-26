#
# This file was generated from the asynchronous client at record_requests.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Implementation of the client for requests inside the NRP repository."""

from yarl import URL

from .connection import Connection
from .request_types import RequestTypeList
from .requests import RequestClient


class RecordRequestsClient(RequestClient):
    """Client for record's requests inside the NRP repository."""

    def __init__(
        self, connection: Connection, requests_url: URL, request_types_url: URL
    ):
        """Initialize the client.

        Normally not used directly,
        use SyncClient().user_records().read(...).requests instead.

        :param connection:              connection to the NRP repository
        :param requests_url:            URL of the requests endpoint for the record
        :param request_types_url:       URL of the request types endpoint for the record
        """
        super().__init__(connection, requests_url)
        self._request_types_url = request_types_url

    def applicable(self, **params: dict[str, str]) -> RequestTypeList:
        """Return all applicable requests (that is those that the current user can apply for)."""
        return self._connection.get(
            url=self._request_types_url,
            result_class=RequestTypeList,
            params=params,
        )

