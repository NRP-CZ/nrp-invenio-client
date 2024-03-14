import typing
from functools import cached_property

if typing.TYPE_CHECKING:
    from nrp_invenio_client.base import NRPInvenioClient


class NRPModelInfo:
    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self):
        return self._data.get("name")

    @property
    def schemas(self):
        return self._data.get("schemas")

    @property
    def links(self):
        return self._data.get("links")

    @property
    def description(self):
        return self._data.get("description")

    @property
    def version(self):
        return self._data.get("version")

    @property
    def features(self):
        return self._data.get("features")

    @property
    def url(self):
        return self._data.get("links", {}).get("self")

    @property
    def user_url(self):
        return self._data.get("links", {}).get("user")

    def to_dict(self):
        return self._data


class NRPRepositoryInfo:
    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self):
        return self._data.get("name")

    @property
    def description(self):
        return self._data.get("description")

    @property
    def version(self):
        return self._data.get("version")

    @property
    def invenio_version(self):
        return self._data.get("invenio_version")

    @property
    def links(self):
        return self._data.get("links")

    @property
    def features(self):
        return self._data.get("features")

    @property
    def transfers(self):
        return self._data.get("transfers")

    def to_dict(self):
        return self._data


class NRPInfoApi:
    """
    Client API for invenio-based NRP repositories.

    Accesses the info endpoint of the repository. As the information
    returned is contained in a repository configuration (invenio.cfg),
    or the code base itself, it is not expected to change at all.
    That's why the information is cached.

    If you need to update the information for whatever reason, create a new
    NRPInvenioClient instance via the clone method.
    """

    def __init__(self, api: "NRPInvenioClient"):
        self._api = api

    @cached_property
    def repository(self) -> NRPRepositoryInfo:
        """
        Get information about the repository
        """
        return NRPRepositoryInfo(self._api.get(path="/.well-known/repository"))

    @cached_property
    def models(self) -> typing.List[NRPModelInfo]:
        return [
            NRPModelInfo(v)
            for v in self._api.get(path="/.well-known/repository/models")
        ]

    def get_model(self, model_name: str):
        model_info = next(
            (model for model in self.models if model.name == model_name), None
        )
        if not model_info:
            model_names = ", ".join(model.name for model in self.models)
            raise KeyError(f"Model {model_name} not found, got {model_names}")
        return model_info
