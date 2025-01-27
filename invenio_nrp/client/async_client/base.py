#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of the client for the NRP repository."""

from functools import partial

from ...config import Config, RepositoryConfig
from ...config.info import RepositoryInfo
from .connection import Connection
from .info import AsyncInfoClient
from .records import RecordClient
from .requests import RequestClient


class AsyncClient(Connection):
    """Client for the NRP repository."""

    def __init__(
        self,
        alias: str | None = None,
        repository: RepositoryConfig | None = None,
        config: Config | None = None,
    ):
        """Initialize the client.

        :param alias:       The alias of the repository to use, will default to the default repository if not provided.
        :param config:      The configuration to use, will default to the configuration from the file if not provided.
        """
        if not config:
            config = Config.from_file()
        if alias:
            repository_config = config.get_repository(alias)
        elif repository:
            repository_config = repository
        else:
            repository_config = config.default_repository

        super().__init__(config, repository_config)

    async def info(self, refresh: bool = False) -> RepositoryInfo:
        """Retrieve info endpoint from the repository.

        :return: The parsed content of the info endpoint

        Note: as the endpoint info rarely changes (only when a new implementation
        is deployed), it is cached in the config object.

        Pass refresh=True to force a refresh and save the config (via client.config.save())
        afterwards.
        """
        return await AsyncInfoClient(
            self._repository_config,
            self,
        ).info(refresh)

    def published_records(self, model: str | None = None) -> RecordClient:
        """Get a client for the records endpoint.

        :param model: The model to use for the records endpoint, will default to all records if not provided.
        :return: A client for the records endpoint
        """
        return RecordClient(
            self,
            create_url=partial(self._repository_config.create_url, model),
            read_url=partial(self._repository_config.read_url, model),
            search_url=partial(self._repository_config.search_url, model),
        )

    def user_records(self, model: str | None = None) -> RecordClient:
        """Get a client for the records endpoint.

        :param model: The model to use for the records endpoint, will default to all records if not provided.
        :return: A client for the records endpoint
        """
        return RecordClient(
            self,
            create_url=partial(self._repository_config.create_url, model),
            read_url=partial(self._repository_config.user_read_url, model),
            search_url=partial(self._repository_config.user_search_url, model),
        )

    def requests(self) -> RequestClient:
        """Get a client for the requests endpoint, giving API for requests that the user has access to.

        :return: API for requests
        """
        return RequestClient(self, self._repository_config.requests_url)
