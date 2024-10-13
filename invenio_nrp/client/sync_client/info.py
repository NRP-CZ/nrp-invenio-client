#
# This file was generated from the asynchronous client at info.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Client for the .well-known/repository endpoint."""
from typing import cast

from pydantic import RootModel

from invenio_nrp.config import RepositoryConfig
from invenio_nrp.types import RepositoryInfo
from invenio_nrp.types.info import ModelInfo, RepositoryInfoLinks

from ..errors import RepositoryClientError, RepositoryCommunicationError
from .connection import Connection


class SyncInfoClient:
    """Client accessing the .well-known/repository endpoint."""

    def __init__(
        self,
        repository_config: RepositoryConfig,
        connection: Connection,
    ):
        self._repository_config = repository_config
        self._connection = connection

    def info(self, refresh=False) -> RepositoryInfo:
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
            info = self._connection.get(
                url=self._repository_config.well_known_repository_url,
                result_class=RepositoryInfo,
            )
            self._repository_config.info = info

            ModelList = RootModel[list[ModelInfo]]
            models = self._connection.get(
                url=self._repository_config.info.links.models,
                result_class=ModelList,
            )
            self._repository_config.info.models = {
                model.name: model for model in models.root
            }

        except (RepositoryClientError, RepositoryCommunicationError):
            # not a NRP based repository, suppose that it is plain invenio rdm
            self._repository_config.info = self._make_rdm_info()

        return cast(RepositoryInfo, self._repository_config.info)

    def _make_rdm_info(self):
        """If repository does not provide the info endpoint, we assume it is a plain invenio rdm."""
        return RepositoryInfo(
            name="RDM repository",
            description="",
            version="unknown",
            invenio_version="unknown",
            transfers=[
                "local-transfer",
            ],
            links=RepositoryInfoLinks(
                records=self._repository_config.url / "api" / "records/",
                user_records=self._repository_config.url / "api" / "user" / "records/",
                requests=self._repository_config.url / "api" / "requests/",
            ),
            models={},
        )
