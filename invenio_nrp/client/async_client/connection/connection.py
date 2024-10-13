#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Asynchronous connection for the NRP client using the aiohttp and aiohttp-retry library."""

import contextlib
import logging
from io import IOBase
from typing import Optional, Type, overload

from aiohttp import ClientSession, TCPConnector
from aiohttp_retry import RetryClient
from pydantic import ValidationError, BaseModel

from invenio_nrp.config import Config, RepositoryConfig

from ...errors import RepositoryCommunicationError, RepositoryError
from .auth import AuthenticatedClientRequest, BearerAuthentication, BearerTokenForHost
from .response import RepositoryResponse
from .retry import ServerAssistedRetry

log = logging.getLogger("invenio_nrp.async_client.connection")

type HttpClient = RetryClient


@contextlib.asynccontextmanager
async def _cast_error():
    """Catch all errors and cast them to Repository*Error."""
    try:
        yield
    except RepositoryError:
        raise
    except Exception as e:
        raise RepositoryCommunicationError(str(e)) from e


class Connection:
    """Pre-configured asynchronous http connection."""

    def __init__(self, config: Config, repository_config: RepositoryConfig):
        """Create a new connection with the given configuration.

        :param config:                  config for all known repositories
        :param repository_config:       config for the repository to connect to
        """
        self._config = config
        self._repository_config = repository_config

        tokens = [
            BearerTokenForHost(host_url=x.url, token=x.token)
            for x in self._config.repositories
            if x.token
        ]
        self.auth = BearerAuthentication(tokens)

    @contextlib.asynccontextmanager
    async def _client(self, idempotent=False) -> HttpClient:
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

    async def get[T](
        self,
        *,
        url: object,
        result_class: Type[T],
        idempotent: bool = True,
        result_context: object = None,
        **kwargs: object,
    ) -> T:
        """Perform a GET request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, should be for GET requests
        :param result_class:        successful response will be parsed to this class
        :param result_context:      context for the result class will be passed to pydantic validation
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network error
        """
        async with self._client(idempotent=idempotent) as client:
            async with _cast_error():
                async with client.get(url, auth=self.auth, **kwargs) as response:
                    return await self._get_call_result(
                        response, result_class, result_context
                    )

    async def post[T](
        self,
        *,
        url,
        json=None,
        data=None,
        idempotent=False,
        result_class: Type[T],
        result_context=None,
        **kwargs,
    ) -> T:
        """Perform a POST request to the repository.

        :param url:                 the url of the request
        :param json:                the json payload of the request (use exactly one of json or data)
        :param data:                the data payload of the request
        :param idempotent:          True if the request is idempotent, normally should be False
        :param result_class:        successful response will be parsed to this class
        :param result_context:      context for the result class will be passed to pydantic validation
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"
        async with self._client(idempotent=idempotent) as client:
            async with _cast_error():
                async with client.post(
                    url, json=json, data=data, auth=self.auth, **kwargs
                ) as response:
                    return await self._get_call_result(
                        response, result_class, result_context
                    )

    async def put[T](
        self,
        *,
        url,
        json=None,
        data=None,
        result_class: Type[T],
        result_context=None,
        **kwargs,
    ) -> T:
        """Perform a PUT request to the repository.

        :param url:                     the url of the request
        :param json:                    the json payload of the request (use exactly one of json or data)
        :param data:                    the data payload of the request
        :param result_class:            successful response will be parsed to this class
        :param result_context:          context for the result class will be passed to pydantic validation
        :param kwargs:                  any kwargs to pass to the aiohttp client
        :return:                        the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        assert (
            json is not None or data is not None
        ), "Either json or data must be provided"
        async with self._client(idempotent=True) as client:
            async with _cast_error():
                async with client.put(
                    url, json=json, data=data, auth=self.auth, **kwargs
                ) as response:
                    return await self._get_call_result(
                        response, result_class, result_context
                    )

    async def put_stream(self, *, url, file: IOBase, **kwargs):
        """Perform a PUT request to the repository with a file.

        :param url:                 the url of the request
        :param file:                the file to send
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    the response (not parsed)

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        async with self._client(idempotent=True) as client:
            async with _cast_error():
                async with client.put(
                    url, data=file, auth=self.auth, **kwargs
                ) as response:
                    await response.raise_for_invenio_status()
                    return response

    async def delete(self, *, url, idempotent=False, **kwargs):
        """Perform a DELETE request to the repository.

        :param url:                 the url of the request
        :param idempotent:          True if the request is idempotent, normally should be False
        :param kwargs:              any kwargs to pass to the aiohttp client
        :return:                    None

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        async with self._client(idempotent=idempotent) as client:
            async with _cast_error():
                async with client.delete(url, auth=self.auth, **kwargs) as response:
                    return await self._get_call_result(response, None, None)

    @overload
    async def _get_call_result[T: BaseModel](
        self, response, result_class: Type[T], result_context
    ) -> T:
        ...

    @overload
    async def _get_call_result(
        self, response, result_class: None, result_context
    ) -> None:
        ...

    async def _get_call_result[T: BaseModel](
        self, response, result_class: Type[T] | None, result_context
    ) -> T | None:
        """Get the result from the response.

        :param response:            the aiohttp response
        :param result_class:        the class to parse the response to
        :param result_context:      the context to pass to the pydantic validation
        :return:                    the parsed result

        :raises RepositoryClientError: if the request fails due to client passing incorrect parameters (HTTP 4xx)
        :raises RepositoryServerError: if the request fails due to server error (HTTP 5xx)
        :raises RepositoryCommunicationError: if the request fails due to network
        """
        await response.raise_for_invenio_status()
        if response.status == 204:
            assert result_class is None
            return None
        json_payload = await response.read()
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
            raise e


def remove_quotes(etag: str) -> Optional[str]:
    """Remove quotes from an etag.

    :param etag:    the etag header
    :return:        the etag without quotes
    """
    if etag is None:
        return None
    return etag.strip('"')


__all__ = ("HttpClient", "Connection")
