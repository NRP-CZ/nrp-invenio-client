import typing
from functools import cached_property

if typing.TYPE_CHECKING:
    from nrp_invenio_client.base import NRPInvenioClient


class NRPModelInfo:
    """
    Information about a model in the repository.
    """

    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self):
        """
        Model name, used in all record's related calls
        """
        return self._data.get("name")

    @property
    def schemas(self):
        """
        A list of json schema identifiers that model's records must conform to.
        """
        return self._data.get("schemas")

    @property
    def links(self):
        """
        Links to the model's records, etc.
        """
        return self._data.get("links")

    @property
    def description(self):
        """
        Human description of the model
        """
        return self._data.get("description")

    @property
    def version(self):
        """
        Current model schema version
        """
        return self._data.get("version")

    @property
    def features(self):
        """
        A list of features implemented in the model (such as drafts, requests, ...)
        """
        return self._data.get("features")

    @property
    def url(self):
        """
        URL of model records
        """
        return self._data.get("links", {}).get("self")

    @property
    def user_url(self):
        """
        URL of model records belonging to the logged-in user (the user bearing the token)
        """
        return self._data.get("links", {}).get("user")

    def to_dict(self):
        """
        Get a json representation of the model
        """
        return self._data


class NRPRepositoryInfo:
    """
    Information about the repository.
    """

    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self):
        """
        Repository name
        """
        return self._data.get("name")

    @property
    def description(self):
        """
        Repository description
        """
        return self._data.get("description")

    @property
    def version(self):
        """
        Version of the software of the repository
        """
        return self._data.get("version")

    @property
    def invenio_version(self):
        """
        Version of invenio libraries as aggregated in the `oarepo` package.
        """
        return self._data.get("invenio_version")

    @property
    def links(self):
        """
        Links to models, ...
        """
        return self._data.get("links")

    @property
    def features(self):
        """
        Features of the repository
        """
        return self._data.get("features")

    @property
    def transfers(self):
        """
        Enabled binary data transfer types
        """
        return self._data.get("transfers")

    def to_dict(self):
        """
        Get a json representation of the repository
        """
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
        """
        Get information about the models in the repository
        """
        return [
            NRPModelInfo(v)
            for v in self._api.get(path="/.well-known/repository/models")
        ]

    def get_model(self, model_name: str):
        """
        Get information about a specific model in the repository
        :param model_name: name of the model
        """
        model_info = next(
            (model for model in self.models if model.name == model_name), None
        )
        if not model_info:
            model_names = ", ".join(model.name for model in self.models)
            raise KeyError(f"Model {model_name} not found, got {model_names}")
        return model_info
