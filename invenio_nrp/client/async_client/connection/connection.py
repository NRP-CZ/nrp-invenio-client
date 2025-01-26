#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Asynchronous connection for the NRP client using the aiohttp and aiohttp-retry library."""

import contextlib
import json as _json
import logging
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
)
from functools import partial
from typing import (
    Any,
    Optional,
    overload,
)

from aiohttp import ClientResponse, ClientSession, TCPConnector
from aiohttp_retry import RetryClient
from attrs import define, field
from cattrs.dispatch import UnstructureHook
from multidict import CIMultiDictProxy
from yarl import URL

from ....config import Config, RepositoryConfig
from ...deserialize import deserialize_rest_response
from ...errors import (
    RepositoryClientError,
    RepositoryCommunicationError,
    RepositoryError,
)
from ..streams.base import DataSink, DataSource
from .auth import AuthenticatedClientRequest, BearerAuthentication, BearerTokenForHost
from .limiter import Limiter
from .response import RepositoryResponse
from .retry import ServerAssistedRetry

log = logging.getLogger("invenio_nrp.async_client.connection")
communication_log = logging.getLogger("invenio_nrp.communication")

HttpClient = RetryClient


class try_until_success:
    def __init__(self, attempts: int):
        self.attempts = attempts
        self.attempt = 0
        self.done = False
        self.failures: list[Exception] = []

    def __iter__(self):
        while not self.done and self.attempt < self.attempts:
            i = self.attempt
            yield self
            assert i != self.attempt, "attempt not attempted"

        if self.done:
            return

        if self.failures:
            raise ExceptionGroup("Failures in HTTP transport", self.failures)

    async def __aenter__(self):
        self.attempt += 1

    async def __aexit__(self, _ext, exc, _tb):
        if exc:
            if isinstance(exc, RepositoryClientError):
                return False
            else:
                self.failures.append(exc)
                return True

        self.done = True


@contextlib.asynccontextmanager
async def _cast_error() -> AsyncIterator[None]:
    """Catch all errors and cast them to Repository*Error."""
    try:
        yield
    except RepositoryError:
        raise
    except Exception as e:
        raise RepositoryCommunicationError(str(e)) from e


class Connection:
    """Pre-configured asynchronous http connection."""

    def __init__(
        self,
        config: Config,
        repository_config: RepositoryConfig,
        number_of_parallel_requests: int = 10,
    ):
        """Create a new connection with the given configuration.

        :param config:                  config for all known repositories
        :param repository_config:       config for the repository to connect to
        """
        self._config = config
        self._repository_config = repository_config
        self._limiter = Limiter(number_of_parallel_requests)

        tokens: list[BearerTokenForHost] = [
            BearerTokenForHost(host_url=x.url, token=x.token)
            for x in self._config.repositories
            if x.token
        ]
        self.auth = BearerAuthentication(tokens)

    @contextlib.asynccontextmanager
    async def _client(
        self, idempotent: bool = False
    ) -> AsyncGenerator[HttpClient, None]:
        """Create a new session with the repository and configure it with the token.

        :return: A new http client
        """
        """
        Create a new session with the repository and configure it with the token.
        :return: A new http client
        """

        connector = TCPConnector(verify_ssl=self._repository_config.verify_tls)
        async with ClientSession(
            request_class=AuthenticatedClientRequest,
            response_class=RepositoryResponse,
            connector=connector,
        ) as session:
            retry_client = RetryClient(
                client_session=session,
                retry_options=ServerAssistedRetry(
                    attempts=self._repository_config.retry_count,
                    start_timeout=self._repository_config.retry_after_seconds,
                ),
            )
            yield retry_client

    async def head(
        self,
        *,
        url: URL,
        use_get: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> CIMultiDictProxy[str]:
        """Perform a HEAD request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, should be for HEAD requests
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    None

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        async def _head(response: ClientResponse) -> CIMultiDictProxy[str]:
            return response.headers

        if use_get:
            return await self._retried("GET", url, _head, idempotent=True,
                                       headers={"Range": "bytes=0-0"})
        else:
            return await self._retried("HEAD", url, _head, idempotent=True)

    async def get[T](
        self,
        *,
        url: URL,
        result_class: type[T],
        result_context: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """Perform a GET request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, should be for GET requests
        :param result_class:        successful response will be parsed to this class
        :param result_context:      context for the result class will be passed to the converter
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network error
        """
        return await self._retried(
            "GET",
            url,
            partial(
                self._get_call_result,
                result_class=result_class,
                result_context=result_context,
            ),
            idempotent=True,
            **kwargs
        )

    async def post[T](
        self,
        *,
        url: URL,
        json: dict[str, Any] | list[Any] | None = None,
        data: bytes | None = None,
        idempotent: bool = False,
        result_class: type[T],
        result_context: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """Perform a POST request to the repository.

        :param url:                 the url of the request
        :param json:                the json payload of the request (use exactly one of json or data)
        :param data:                the data payload of the request
        :param idempotent:          True if the request is idempotent, normally should be False
        :param result_class:        successful response will be parsed to this class
        :param result_context:      context for the result class will be passed to the converter
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"

        return await self._retried(
            "POST",
            url,
            partial(
                self._get_call_result,
                result_class=result_class,
                result_context=result_context,
            ),
            idempotent=idempotent,
            json=json,
            data=data,
            **kwargs
        )

    async def put[T](
        self,
        *,
        url: URL,
        json: dict[str, Any] | list[Any] | None = None,
        data: bytes | None = None,
        result_class: type[T],
        result_context: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """Perform a PUT request to the repository.

        :param url:                     the url of the request
        :param json:                    the json payload of the request (use exactly one of json or data)
        :param data:                    the data payload of the request
        :param result_class:            successful response will be parsed to this class
        :param result_context:          context for the result class will be passed to the converter
        :param kwargs:                  any kwargs to pass to the aiohttp client
        :return:                        the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"

        return await self._retried(
            "PUT",
            url,
            partial(
                self._get_call_result,
                result_class=result_class,
                result_context=result_context,
            ),
            idempotent=True,
            json=json,
            data=data,
            **kwargs,
        )

    async def put_stream(
        self,
        *,
        url: URL,
        source: DataSource,
        open_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> ClientResponse:
        """Perform a PUT request to the repository with a file.

        :param url:                 the url of the request
        :param file:                the file to send
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the response (not parsed)

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """

        async def _put(response: ClientResponse) -> ClientResponse:
            return response

        return await self._retried(
            "PUT",
            url,
            _put,
            idempotent=True,
            data=partial(source.open, **(open_kwargs or {})),
            **kwargs
        )

    async def get_stream(
        self,
        *,
        url: URL,
        sink: DataSink,
        offset: int = 0,
        size: int | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Perform a GET request to the repository and write the response to a sink.

        :param url:                 the url of the request
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network error
        """
        
        async def _copy_stream(response: ClientResponse) -> None:
            chunk = await sink.open_chunk(offset=offset)
            try:
                async for data in response.content.iter_any():
                    await chunk.write(data)
            finally:
                await chunk.close()
        
        if size is not None:
            range_header = f"bytes={offset}-{offset + size - 1}"
        else:
            range_header = f"bytes={offset}-"
        
        await self._retried(
            "GET",
            url,
            _copy_stream,
            idempotent=True,
            headers={"Range": range_header},
            **kwargs
        )

    async def delete(
        self,
        *,
        url: URL,
        idempotent: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Perform a DELETE request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, normally should be False
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    None

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        return await self._retried(
            "DELETE",
            url,
            None,
            idempotent=idempotent,
            **kwargs
        )

    @overload
    async def _get_call_result[T](
        self,
        response: ClientResponse,
        result_class: type[T],
        result_context: dict[str, Any] | None,
    ) -> T: ...

    @overload
    async def _get_call_result(
        self,
        response: ClientResponse,
        result_class: None,
        result_context: dict[str, Any] | None,
    ) -> None: ...

    async def _get_call_result[T](
        self,
        response: ClientResponse,
        result_class: type[T] | None,
        result_context: dict[str, Any] | None,
    ) -> T | None:
        """Get the result from the response.

        :param response:            the aiohttp response
        :param result_class:        the class to parse the response to
        :param result_context:      the context to pass to the converter
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        await response.raise_for_invenio_status()  # type: ignore
        if response.status == 204:
            assert result_class is None
            return None
        json_payload = await response.read()
        assert result_class is not None
        if issubclass(result_class, ClientResponse):
            return response
        etag = remove_quotes(response.headers.get("ETag"))
        return deserialize_rest_response(
            self, communication_log, json_payload, result_class, result_context, etag
        )

    @overload
    async def _retried[T](
        self,
        method: str,
        url: URL,
        callback: Callable[[ClientResponse], Awaitable[T]],
        idempotent: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> T: ...
    
    @overload
    async def _retried(
        self,
        method: str,
        url: URL,
        callback: None,
        idempotent: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> None: ...

    async def _retried[T](
        self,
        method: str,
        url: URL,
        callback: Callable[[ClientResponse], Awaitable[T]] | None,
        idempotent: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> T | None:
        """Log the start of a request and retry it if necessary."""
        json = kwargs.get("json")
        if json is not None and callable(json):
            json = json()
            kwargs["json"] = json

        data = kwargs.get("data")

        if communication_log.isEnabledFor(logging.INFO):
            communication_log.info("%s %s", method.upper(), url)
            if json is not None:
                communication_log.info("%s", _json.dumps(json))
            if data is not None:
                communication_log.info("(stream)")

        for attempt in try_until_success(
            self._repository_config.retry_count if idempotent else 1
        ):
            actual_data = None
            if data is not None and callable(data):
                actual_data = await data()
                kwargs["data"] = actual_data
            try:
                async with (
                    attempt,
                    self._limiter,
                    self._client(idempotent=True) as client,
                    _cast_error(),
                    client.request(method, url, auth=self.auth, **kwargs) as response,
                ):
                    await response.raise_for_invenio_status()  # type: ignore
                    if callback is not None:
                        return await callback(response)
                    return None
            finally:
                if actual_data is not None and hasattr(actual_data, "close"):
                    actual_data.close()

        raise Exception("unreachable")


def remove_quotes(etag: str | None) -> Optional[str]:
    """Remove quotes from an etag.

    :param etag:    the etag header
    :return:        the etag without quotes
    """
    if etag is None:
        return None
    if etag.startswith("W/"):
        etag = etag[2:]
    return etag.strip('"')


def connection_unstructure_hook(data: Any, previous: UnstructureHook) -> Any:
    ret = previous(data)
    ret.pop("_connection", None)
    ret.pop("_etag", None)
    return ret


@define(kw_only=True)
class ConnectionMixin:
    """A mixin for classes that are a result of a REST API call."""

    _connection: Connection = field(init=False, default=None)
    """Connection is automatically injected"""

    _etag: Optional[str] = field(init=False, default=None)
    """etag is automatically injected if it was returned by the repository"""

    def _set_connection_params(
        self, connection: Connection, etag: Optional[str] = None
    ) -> None:
        """Set the connection and etag."""
        self._connection = connection
        self._etag = etag

    def _etag_headers(self) -> dict[str, str]:
        """Return the headers with the etag if it was returned by the repository."""
        headers: dict[str, str] = {}
        if self._etag:
            headers["If-Match"] = self._etag
        return headers


__all__ = ("HttpClient", "Connection")
