#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Synchronous low-level connection."""

import contextlib
import json
import logging
from io import IOBase
from typing import Any, Generator, Optional, Type, overload

import requests
from pydantic import BaseModel, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from yarl import URL

from invenio_nrp.client.async_client.connection.auth import BearerTokenForHost
from invenio_nrp.client.errors import (
    RepositoryClientError,
    RepositoryCommunicationError,
    RepositoryError,
    RepositoryServerError,
)
from invenio_nrp.client.sync_client.connection.auth import BearerAuthentication
from invenio_nrp.config import Config, RepositoryConfig

log = logging.getLogger("invenio_nrp.sync_client.connection")


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


def raise_for_invenio_status(response: requests.Response) -> None:
    """Raise an exception if the response is not successful."""
    if not response.ok:
        payload = response.text
        try:
            payload = json.loads(payload)
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
            adapter = HTTPAdapter(max_retries=retry)
        else:
            adapter = HTTPAdapter()

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

    def get[T](
        self,
        *,
        url: URL,
        idempotent: bool = True,
        result_class: Type[T],
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
        with (
            self._client(idempotent=idempotent) as client,
            _cast_error(),
            client.get(url, **kwargs) as response,
        ):
            return self._get_call_result(response, result_class, result_context)

    def post[T](
        self,
        *,
        url: URL,
        json: dict | list | None = None,
        data: bytes | None = None,
        idempotent: bool = False,
        result_class: Type[T],
        result_context: dict | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
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
        with (
            self._client(idempotent=idempotent) as client,
            _cast_error(),
            client.post(url, json=json, data=data, **kwargs) as response,
        ):
            return self._get_call_result(response, result_class, result_context)

    def put[T](
        self,
        *,
        url: URL,
        json: dict | list | None = None,
        data: bytes | None = None,
        result_class: Type[T],
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
        with (
            self._client(idempotent=True) as client,
            _cast_error(),
            client.put(url, json=json, data=data, **kwargs) as response,
        ):
            return self._get_call_result(response, result_class, result_context)

    def put_stream(
        self,
        *,
        url: URL,
        file: IOBase,
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
        with (
            self._client(idempotent=True) as client,
            _cast_error(),
            client.put(url, data=file, **kwargs) as response,
        ):
            raise_for_invenio_status(response)
            return response

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
        with (
            self._client(idempotent=idempotent) as client,
            _cast_error(),
            client.delete(url, **kwargs) as response,
        ):
            return self._get_call_result(response, None, None)

    @overload
    def _get_call_result(
        self,
        response: requests.Response,
        result_class: None,
        result_context: dict | None,
    ) -> None: ...

    @overload
    def _get_call_result[T: BaseModel](
        self,
        response: requests.Response,
        result_class: Type[T],
        result_context: dict | None,
    ) -> T: ...

    def _get_call_result[T: BaseModel](
        self,
        response: requests.Response,
        result_class: Type[T] | None,
        result_context: dict | None,
    ) -> T | None:
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
            assert result_class is None
            return None
        json_payload = response.text
        assert result_class is not None
        try:
            return result_class.model_validate_json(
                json_payload,
                strict=True,
                context={
                    **(result_context or {}),
                    "etag": remove_quotes(response.headers.get("ETag")),
                    "connection": self,
                },
            )
        except ValidationError as e:
            log.error("Error validating %s with %s", json_payload, result_class)
            log.error(e)
            raise e


def remove_quotes(etag: str) -> Optional[str]:
    if etag is None:
        return None
    return etag.strip('"')


__all__ = ("Connection",)
