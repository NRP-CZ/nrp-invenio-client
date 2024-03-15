import contextlib
import os
import urllib
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from enum import Enum
from functools import cached_property
from io import IOBase
from pathlib import Path
from typing import ContextManager, Iterable, Optional, Protocol, TypeAlias

import httpx
import tenacity

from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.errors import (
    NRPInvenioClientInvalidContentTypeError,
    NRPInvenioClientNotFoundError,
    NRPInvenioClientServerBusyError,
)
from nrp_invenio_client.info import NRPInfoApi
from nrp_invenio_client.records import NRPRecordsApi
from nrp_invenio_client.search import NRPSearchRequest, NRPSearchResponse

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


class ResponseFormat(Enum):
    JSON = "json"
    "The response is expected to be JSON"

    RAW = "raw"
    "The response is raw data, will return httpx.Response object"


class _RequestWithRetries(Protocol):
    def __call__(
        self,
        *,
        path: str,
        method: str,
        format: ResponseFormat,
        data: JSON | IOBase | bytes = None,
        headers=None,
    ) -> JSON | IOBase: ...


class NRPInvenioClient:
    """
    Client API for invenio-based NRP repositories
    """

    def __init__(
        self,
        server_url: str,
        token: str = None,
        verify: str | bool = True,
        retry_count=10,
        retry_interval=10,
        repository_config: NRPConfig = None,
    ):
        """
        Initialize the API client. Note: the parameters here are fixed for the lifetime of the client, can not be changed later.

        :param server_url:      base url of the invenio server
        :param token:           authentication token, can be skipped for anonymous access
        :param verify:          verify the server certificate
        :param retry_count:     number of retries for GET requests
        :param retry_interval:  interval between retries for GET requests, if server does not respond with a Retry-After header
        """
        self._repository_config = repository_config
        self._server_url = server_url
        self._token = token
        self._verify = verify
        self._retry_interval = retry_interval
        self._retry_count = retry_count

        self._httpx_client = httpx.Client(verify=self._verify, http2=True)
        self._request_with_retries: _RequestWithRetries = tenacity.retry(  # type: ignore
            stop=tenacity.stop_after_attempt(retry_count),
            # TODO: custom wait based on server response
            wait=tenacity.wait_exponential(min=retry_interval, max=retry_interval * 10),
            retry=tenacity.retry_if_exception_type(NRPInvenioClientServerBusyError),
            reraise=True,
        )(
            self._internal_request
        )

    @classmethod
    def from_config(
        cls, alias=None, config_or_config_file: Optional[str | Path | NRPConfig] = None
    ) -> "NRPInvenioClient":
        """
        Create a new NRPInvenioClient instance from a configuration file.

        :param alias:           use this repository alias from the config file
        :param config_or_config_file:     override the default location of the config file or pass the config object directly
        :return:                new NRPInvenioClient instance
        """
        if isinstance(config_or_config_file, NRPConfig):
            config = config_or_config_file
        else:
            config = NRPConfig()
            config.load(config_or_config_file)

        repository_config = config.get_repository_config(alias)
        return cls(
            server_url=os.environ.get("NRP_INVENIO_CLIENT_URL", repository_config.url),
            token=os.environ.get("NRP_INVENIO_CLIENT_TOKEN", repository_config.token),
            verify=bool_or_str(
                os.environ.get(
                    "NRP_INVENIO_CLIENT_VERIFY",
                    repository_config.verify,
                )
            ),
            retry_count=int(
                os.environ.get(
                    "NRP_INVENIO_CLIENT_RETRY_COUNT", repository_config.retry_count
                )
            ),
            retry_interval=int(
                os.environ.get(
                    "NRP_INVENIO_CLIENT_RETRY_INTERVAL",
                    repository_config.retry_interval,
                )
            ),
            repository_config=repository_config,
        )

    @property
    def repository_config(self):
        return self._repository_config

    #
    # Specialised endpoints
    #
    @cached_property
    def info(self) -> NRPInfoApi:
        return NRPInfoApi(self)

    @cached_property
    def records(self) -> NRPRecordsApi:
        return NRPRecordsApi(self)

    def search_request(
        self,
        models=None,
        page=None,
        size=None,
        order_by=None,
        fields=None,
        published=None,
        drafts=None,
        query=None,
    ) -> NRPSearchRequest:
        request = NRPSearchRequest(self, models)

        if page is not None:
            request.page(page)
        if size is not None:
            request.size(size)
        if order_by is not None:
            request.order_by(*order_by)
        if fields is not None:
            request.fields(*fields)
        if published:
            request.published()
        if drafts:
            request.drafts()
        if query is not None:
            request.query(query)

        return request

    def search(self, models=None, **kwargs) -> NRPSearchResponse:
        """
        Shortcut method for creating and executing a search request.
        See NRPSearchRequest for more details.

        :param models: list of models, if none provided all models will be searched
        :return: search response
        """
        return self.search_request(models=models, **kwargs).execute()

    def scan(self, models=None, **kwargs) -> ContextManager[Iterable[JSON]]:
        """
        Shortcut method for creating and executing a search request and returning all results.
        See NRPSearchRequest for more details.

        :param models: list of models, if none provided all models will be searched
        :return: generator of search results
        """
        return self.search_request(models=models, **kwargs).scan()

    def clone(self):
        """
        Create a new NRPInvenioClient instance with the same parameters as this instance.
        """
        return NRPInvenioClient(
            server_url=self._server_url,
            token=self._token,
            verify=self._verify,
            retry_interval=self._retry_interval,
            retry_count=self._retry_count,
        )

    #
    # Generic http methods
    #

    def get(self, path: str, format: ResponseFormat = None, headers=None, params=None):
        return self._request_with_retries(
            path=path, method="GET", format=format, headers=headers, params=params
        )

    def post(
        self,
        path: str,
        data: JSON | IOBase,
        format: ResponseFormat = None,
        headers=None,
        params=None,
    ):
        return self._request_with_retries(
            path=path,
            method="POST",
            format=format,
            data=data,
            headers=headers,
            params=params,
        )

    def put(
        self,
        path: str,
        data: JSON | IOBase,
        format: ResponseFormat = None,
        headers=None,
        params=None,
    ):
        return self._request_with_retries(
            path=path,
            method="PUT",
            format=format,
            data=data,
            headers=headers,
            params=params,
        )

    def delete(self, path: str, headers=None):
        return self._request_with_retries(
            path=path, method="DELETE", headers=headers, format=ResponseFormat.JSON
        )

    @contextlib.contextmanager
    def stream(self, path: str, headers=None):
        with self._httpx_client.stream(
            method="GET",
            url=urllib.parse.urljoin(self._server_url, path),
            headers=headers,
            follow_redirects=True,
        ) as stream:
            yield stream

    #
    # Internal methods
    #

    def _internal_request(
        self,
        *,
        path: str,
        method: str,
        format: ResponseFormat,
        data: JSON | IOBase | bytes = None,
        headers=None,
        params=None,
    ):
        request_kwargs = self._get_request_kwargs(data, headers)

        full_url = urllib.parse.urljoin(self._server_url, path)

        try:
            response = self._httpx_client.request(
                method=method, url=full_url, params=params, **request_kwargs
            )
            response.raise_for_status()
            return self._decode_response(response, format)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NRPInvenioClientNotFoundError(
                    full_url,
                    f"URL {full_url} not found",
                )
            if e.response.status_code in (429, 503):
                retry_after = self._get_retry_interval(
                    e.response.headers, self._retry_interval
                )
                raise NRPInvenioClientServerBusyError(
                    full_url,
                    f"Server is too busy at url {full_url}, retry after {retry_after} seconds",
                    retry_after,
                )
            raise
        except:
            import traceback

            traceback.print_exc()
            raise

    def _decode_response(self, response: httpx.Response, format: ResponseFormat):
        if response.status_code == 204:
            return {}

        response_content_type = (
            response.headers.get("Content-Type").split(";")[0].strip()
        )

        if format is None:
            if response_content_type == "application/json":
                format = ResponseFormat.JSON

        match format:
            case ResponseFormat.JSON:
                try:
                    return response.json()
                except ValueError:
                    raise NRPInvenioClientInvalidContentTypeError(
                        response.url,
                        "Invalid JSON",
                        response_content_type,
                    )
            case ResponseFormat.RAW:
                return response
            case _:
                raise NRPInvenioClientInvalidContentTypeError(
                    response.url,
                    f"No response format parser for content type {response_content_type}",
                    response_content_type,
                )

    def _get_request_kwargs(self, data, headers):
        request_kwargs = {}
        if headers:
            request_kwargs["headers"] = {**headers}
        else:
            request_kwargs["headers"] = {}
        if self._token:
            request_kwargs["headers"]["Authorization"] = f"Bearer {self._token}"
        if data:
            if isinstance(data, (IOBase, bytes)):
                request_kwargs["content"] = data
            else:
                request_kwargs["json"] = data
        request_kwargs.setdefault("follow_redirects", True)
        return request_kwargs

    def _get_retry_interval(self, headers, default_retry_interval):
        retry_after = headers.get("Retry-After", default_retry_interval)
        try:
            return float(retry_after)
        except ValueError:
            pass

        # might be a HTTP Date
        try:
            return (parsedate_to_datetime(retry_after) - datetime.now()).total_seconds()
        except:
            pass

        return default_retry_interval


def bool_or_str(x: bool | str):
    if isinstance(x, bool):
        return x

    if x.lower() in ("true", "1", "yes", "on"):
        return True
    if x.lower() in ("false", "0", "no", "off"):
        return False

    return x
