#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Synchronous low-level connection."""

import contextlib
import json as _json
import logging
from collections.abc import Callable, Generator
from functools import partial
from typing import Any, Optional

import requests
from attrs import define, field
from cattrs.dispatch import UnstructureHook
from requests import adapters
from requests.structures import CaseInsensitiveDict
from urllib3.util import Retry
from yarl import URL

from ....config import Config, RepositoryConfig
from ...auth import BearerTokenForHost
from ...deserialize import deserialize_rest_response
from ...errors import (
    RepositoryClientError,
    RepositoryCommunicationError,
    RepositoryError,
    RepositoryServerError,
)
from ..streams.base import DataSink, DataSource
from .auth import BearerAuthentication
from .aws_limits import MINIMAL_DOWNLOAD_PART_SIZE, adjust_download_multipart_params

log = logging.getLogger("invenio_nrp.sync_client.connection")
communication_log = logging.getLogger("invenio_nrp.communication")


@contextlib.contextmanager
def _cast_error() -> Generator[None, None, None]:
    """Catch all errors and cast them to Repository*Error.

    :return:
    """
    try:
        yield
    except RepositoryError:
        raise
    except Exception as e:
        raise RepositoryCommunicationError(str(e)) from e


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

    def __enter__(self):
        self.attempt += 1

    def __exit__(self, _ext, exc, _tb):
        if exc:
            if isinstance(exc, RepositoryClientError):
                return False
            else:
                self.failures.append(exc)
                return True

        self.done = True


def raise_for_invenio_status(response: requests.Response) -> None:
    """Raise an exception if the response is not successful."""
    if not response.ok:
        payload = response.text
        try:
            payload = _json.loads(payload)
        except ValueError:
            payload = {
                "status": response.status_code,
                "reason": payload,
            }

        if response.status_code >= 500:
            raise RepositoryServerError(response.request, payload)
        elif response.status_code >= 400:
            raise RepositoryClientError(response.request, payload)
        raise RepositoryCommunicationError(response.request, payload)


class Connection:
    """Low-level synchronous connection to the repository."""

    def __init__(self, config: Config, repository_config: RepositoryConfig):
        """Initialize the connection."""
        self._config = config
        self._repository_config = repository_config

        tokens = [
            BearerTokenForHost(host_url=x.url, token=x.token)
            for x in self._config.repositories
            if x.token
        ]
        self.auth = BearerAuthentication(tokens)

    @contextlib.contextmanager
    def _client(
        self, idempotent: bool = False
    ) -> Generator[requests.Session, None, None]:
        """Create a new session with the repository and configure it with the token.

        :return: A new http client
        """
        """
        Create a new session with the repository and configure it with the token.
        :return: A new http client
        """
        if idempotent:
            retry = Retry(
                total=self._repository_config.retry_count,
                backoff_factor=self._repository_config.retry_after_seconds,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = adapters.HTTPAdapter(max_retries=retry)
        else:
            adapter = adapters.HTTPAdapter()

        session = requests.Session()
        session.auth = self.auth
        session.mount("https://", adapter)
        session.verify = self._repository_config.verify_tls

        yield session

    @property
    def config(self) -> Config:
        """Configuration of client."""
        return self._config

    @property
    def repository_config(self) -> RepositoryConfig:
        """Configuration of the repository."""
        return self._repository_config

    def head(
        self,
        *,
        url: URL,
        use_get: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> CaseInsensitiveDict[str]:
        """Perform a HEAD request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, should be for HEAD requests
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    None

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        def _head(response: requests.Response) -> CaseInsensitiveDict[str]:
            return response.headers

        if use_get:
            return self._retried("GET", url, _head, idempotent=True,
                                       headers={"Range": "bytes=0-0"})
        else:
            return self._retried("HEAD", url, _head, idempotent=True)

    def get[T](
        self,
        *,
        url: URL,
        idempotent: bool = True,
        result_class: type[T],
        result_context: dict | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """Perform a GET request to the repository.

        :param url:
        :param idempotent:
        :param result_class:
        :param result_context:
        :param kwargs:
        :return:

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network error
        """
        return self._retried(
            "GET",
            url,
            partial(
                self._get_call_result,
                result_class=result_class,
                result_context=result_context,
            ),
            idempotent=True,
            **kwargs,
        )

    def post[T](
        self,
        *,
        url: URL,
        json: dict | list | None = None,
        data: bytes | None = None,
        idempotent: bool = False,
        result_class: type[T] | None,
        result_context: dict | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T | None:
        """Perform a POST request to the repository.

        :param url:
        :param json:
        :param data:
        :param idempotent:
        :param result_class:
        :param result_context:
        :param kwargs:
        :return:

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"

        if result_class:
            return self._retried(
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
                **kwargs,
            )
        else:
            return self._retried(
                "POST",
                url,
                self._check_empty_call_result,
                idempotent=idempotent,
                json=json,
                data=data,
                **kwargs,
            )

    def put[T](
        self,
        *,
        url: URL,
        json: dict | list | None = None,
        data: bytes | None = None,
        result_class: type[T],
        result_context: dict | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """Perform a PUT request to the repository.

        :param url:
        :param json:
        :param data:
        :param result_class:
        :param result_context:
        :param kwargs:
        :return:

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"


        return self._retried(
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

    def put_stream(
        self,
        *,
        url: URL,
        source: DataSource,
        open_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> requests.Response:
        """Perform a PUT request to the repository with a file.

        :param url:
        :param file:
        :param kwargs:
        :return:

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """

        def _put(response: requests.Response) -> requests.Response:
            raise_for_invenio_status(response)
            return response

        return self._retried(
            "PUT",
            url,
            _put,
            idempotent=True,
            data=partial(source.open, **(open_kwargs or {})),
            **kwargs
        )


    def get_stream(
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

        def _copy_stream(response: requests.Response) -> None:
            chunk = sink.open_chunk(offset=offset)
            try:
                for data in response.iter_content(chunk_size=16384):
                    chunk.write(data)
            finally:
                chunk.close()
        
        if size is not None:
            range_header = f"bytes={offset}-{offset + size - 1}"
        else:
            range_header = f"bytes={offset}-"
        
        return self._retried(
            "GET",
            url,
            _copy_stream,
            idempotent=True,
            headers={"Range": range_header},
            stream=True,
            **kwargs
        )

    def delete(
        self,
        *,
        url: URL,
        idempotent: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Perform a DELETE request to the repository.

        :param url:
        :param idempotent:
        :param kwargs:
        :return:
        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        return self._retried(
            "DELETE",
            url,
            self._check_empty_call_result,
            idempotent=idempotent,
            **kwargs
        )


    def _check_empty_call_result(self, response: requests.Response) -> None:
        raise_for_invenio_status(response)
        if response.status_code == 204:
            return None  # No content
        raise RepositoryCommunicationError("Expected empty response")

    def _get_call_result[T](
        self,
        response: requests.Response,
        result_class: type[T],
        result_context: dict | None,
    ) -> T:
        """Get the result from the response.

        :param response:
        :param result_class:
        :param result_context:
        :return:

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        raise_for_invenio_status(response)
        if response.status_code == 204:
            raise RepositoryCommunicationError("Expected response with content")

        json_payload = response.content
        etag = remove_quotes(response.headers.get("ETag"))
        return deserialize_rest_response(
            self, communication_log, json_payload, result_class, result_context, etag
        )

    def _retried[T](
        self,
        method: str,
        url: URL,
        callback: Callable[[requests.Response], T],
        idempotent: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
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
                actual_data = data()
                kwargs["data"] = actual_data
            try:
                with (
                    attempt,
                    self._client(idempotent=True) as client,
                    _cast_error(),
                    client.request(method, str(url), auth=self.auth, **kwargs) as response,
                ):
                    raise_for_invenio_status(response)  # type: ignore
                    if callback is not None:
                        return callback(response)
                    return None
            finally:
                if actual_data is not None and hasattr(actual_data, "close"):
                    actual_data.close()

        raise Exception("unreachable")


    def download_file(
        self, url: URL, sink: DataSink, 
        parts: int | None =None, 
        part_size : int | None = None) -> None:

        try:
            headers = self.head(url=url)
        except RepositoryClientError:
            # The file is not available for HEAD. This is the case for S3 files
            # where the file is a pre-signed request. We'll try to download the headers
            # with a GET request with a range header containing only the first byte.
            headers = self.head(url=url, use_get=True)

        size = 0
        location = URL(headers.get('Location', url))
        
        if "Content-Length" in headers:
            size = int(headers["Content-Length"])
            sink.allocate(size)

        if (
            size
            and size > MINIMAL_DOWNLOAD_PART_SIZE
            and headers.get("Accept-Ranges") == 'bytes'
        ):
            self._download_multipart(location, sink, size, parts, part_size)
        else:
            self._download_single(location, sink)

    def _download_single(self, url: URL, sink: DataSink) -> None:
        self.get_stream(url=url, sink=sink, offset=0)

    def _download_multipart(
        self, url: URL, sink: DataSink, size: int, parts: int | None = None, part_size: int | None = None
    ) -> None:
        adjusted_parts, adjusted_part_size = adjust_download_multipart_params(size, parts, part_size)

        for i in range(adjusted_parts):
            start = i * adjusted_part_size
            size = min((i + 1) * adjusted_part_size, size) - start
            self.get_stream(
                url=url, sink=sink, offset=start, size=size
            )


def remove_quotes(etag: str | None) -> Optional[str]:
    if etag is None:
        return None
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


__all__ = ("Connection",)
