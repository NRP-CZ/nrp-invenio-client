#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Client for the .well-known/repository endpoint."""

from typing import cast

from pydantic import RootModel

from invenio_nrp.config import RepositoryConfig
from invenio_nrp.types import RepositoryInfo
from invenio_nrp.types.info import ModelInfo

from ..errors import RepositoryClientError, RepositoryCommunicationError
from ..rdm import _make_rdm_info
from .connection import Connection


class AsyncInfoClient:
    """Client accessing the .well-known/repository endpoint."""

    def __init__(
        self,
        repository_config: RepositoryConfig,
        connection: Connection,
    ):
        """Initialize the client."""
        self._repository_config = repository_config
        self._connection = connection

    async def info(self, refresh: bool = False) -> RepositoryInfo:
        """Retrieve info endpoint from the repository.

        :return: The parsed content of the info endpoint

        Note: as the endpoint info rarely changes (only when a new implementation
        is deployed), it is cached in the config object.

        Pass refresh=True to force a refresh and save the config (via client.config.save())
        afterwards.
        """
        if self._repository_config.info and not refresh:
            return self._repository_config.info

        try:
            info = await self._connection.get(
                url=self._repository_config.well_known_repository_url,
                result_class=RepositoryInfo,
            )
            self._repository_config.info = info

            ModelList = RootModel[list[ModelInfo]]
            models = await self._connection.get(
                url=self._repository_config.info.links.models,
                result_class=ModelList,
            )
            self._repository_config.info.models = {
                model.name: model for model in models.root
            }

        except (RepositoryClientError, RepositoryCommunicationError):
            # not a NRP based repository, suppose that it is plain invenio rdm
            import traceback
            traceback.print_exc()
            self._repository_config.info = _make_rdm_info(self._repository_config.url)

        return cast(RepositoryInfo, self._repository_config.info)
