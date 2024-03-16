import typing
from urllib.parse import urljoin

from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.files import NRPFile, NRPRecordFiles
from nrp_invenio_client.requests import NRPRecordRequests
from nrp_invenio_client.utils import (
    get_mid,
    is_doi,
    is_mid,
    is_url,
    resolve_record_doi,
    resolve_repository_url,
)

if typing.TYPE_CHECKING:
    from nrp_invenio_client.base import NRPInvenioClient


class NRPRecord:
    """
    A record in the repository. It contains the metadata and links of the record
    and might contain references to files and requests.

    This class is not meant to be instantiated directly, use the `get/create` methods of
    `NRPRecordsApi` instead.
    """

    def __init__(
        self,
        *,
        client: "NRPInvenioClient",
        model: str,
        record_id: typing.Optional[str] = None,
        data: typing.Optional[dict] = None,
        files: typing.Optional[dict] = None,
        requests: typing.Optional[dict] = None,
    ):
        self._client = client
        self._model = model
        self._record_id = record_id
        self._data = data
        self._files = NRPRecordFiles(
            self,
            **{
                metadata["key"]: NRPFile(
                    record=self, key=metadata["key"], data=metadata
                )
                for metadata in (files or [])
            },
        )
        self._requests = NRPRecordRequests(
            self, self._data.get("request_types", []), requests or []
        )

    @property
    def data(self):
        """
        The whole data of the record (metadata, links, etc.)
        """
        return self._data

    @property
    def errors(self):
        return self._data.get("errors", None)

    def to_dict(self, files=True, requests=True, mid=True):
        """
        Returns json representation of the record
        """
        ret = {
            **self._data,
        }
        if mid:
            ret["mid"] = self.record_id

        if files and self._files:
            ret["files"] = self._files.to_dict()
        if requests and self._requests:
            ret["requests"] = self._requests.to_dict()
        return ret

    @property
    def metadata(self):
        """
        If the record has a metadata section, return that. Otherwise return the whole data.
        """
        if not self.data:
            return {}
        return self._data.get("metadata", None) or self._data

    @property
    def files(self) -> NRPRecordFiles:
        """
        Returns the files of the record
        """
        return self._files

    @property
    def requests(self) -> NRPRecordRequests:
        """
        Returns the requests of the record
        """
        return self._requests

    @property
    def links(self):
        """
        The content of links section, such as "self" or "draft"
        """
        return self._data["links"]

    @property
    def record_id(self):
        """
        Returns the id of the record in the form of "model/id" or "draft/model/id"
        """
        if self.links.get("self") == self.links.get("draft"):
            return f"draft/{self._model}/{self._record_id}"
        else:
            return f"{self._model}/{self._record_id}"

    def clear_data(self):
        """
        Removes all the data from the record except the links, parent, revision_id and id
        """
        for k in list(self._data.keys()):
            if k not in ("links", "parent", "revision_id", "id"):
                del self._data[k]

    def save(self):
        """
        Saves the metadata of the record to the repository
        """
        ret = self._client.put(
            self.links["self"],
            data=self.to_dict(files=False, requests=False, mid=False),
            headers={
                "Content-Type": "application/json",
                "If-Match": str(self._data["revision_id"]),
            },
        )
        self._data = ret

    def delete(self):
        """
        Deletes the record from the repository
        """
        return self._client.delete(self.links["self"], headers={})

    def publish(self, version=None):
        """
        Publishes a draft record and updates self to contain the published record
        :return: The published record
        """
        if version is not None:
            # TODO: check that the version has not been used yet
            self._data["version"] = version
            self.save()
        ret = self._client.post(self.links["publish"], None)

        return NRPRecord(
            client=self._client,
            model=self._model,
            record_id=ret["id"],
            data=ret,
        )

    def edit(self):
        """
        Edits a published record - creates a draft copy and returns that
        :return: The draft record
        """
        ret = self._client.post(self.links["versions"], None)

        rec = NRPRecord(
            client=self._client,
            model=self._model,
            record_id=ret["id"],
            data=ret,
        )
        # copy files from the previous version
        # TODO: do not have a link for that yet
        return rec

    def __str__(self):
        return f"NRPRecord[{self._model}/{self._record_id}]"


class NRPRecordsApi:
    """
    API for working with records in the repository. Use the `records` property of `NRPInvenioClient` to get an instance.
    Example:
    ```
        client = NRPInvenioClient.from_config()
        records = client.records
        record = records.get("model/id")
    ```
    """

    def __init__(self, api: "NRPInvenioClient"):
        self._api = api

    def get(
        self,
        mid: str | typing.Tuple[str, str],
        include_files=False,
        include_requests=False,
    ) -> NRPRecord:
        """
        Returns a record by its id

        :param mid: Either a string mid "model/id within model" or a tuple (model, id within model).
                    For drafts, the mid is "draft/model/id within model" or tuple
                    ("draft", model, id within model)
        :param include_files: If True, metadata the files of the record are fetched as well
                              and included in the returned object. This adds another http request
        :param include_requests: If True, the requests of the record are fetched as well included in the returned object.
                                This adds another http request
        :return: The JSON data of the record
        """
        if isinstance(mid, str):
            mid = mid.split("/")
        elif not isinstance(mid, (tuple, list)):
            raise ValueError(f"Invalid mid {mid}. Must be either a string or a tuple")

        match len(mid):
            case 2:
                prefix = None
                model, record_id = mid
            case 3:
                prefix, model, record_id = mid
            case _:
                raise ValueError(
                    f'Invalid mid tuple {mid}. Must be either (model, id) or ("draft", model, id)'
                )

        model_info = self._api.info.get_model(model)

        match prefix:
            case "draft":
                url = urljoin(model_info.links["api"], f"{record_id}/draft")
            case None:
                url = urljoin(model_info.links["api"], record_id)
            case _:
                raise ValueError(
                    f"Invalid prefix {prefix} in \"mid\". Must be either 'draft' or not used at all"
                )

        metadata = self._api.get(url)

        files = {}
        if include_files and "files" in metadata["links"]:
            files = self._api.get(metadata["links"]["files"])["entries"]

        requests = {}
        if include_requests and "requests" in metadata["links"]:
            requests = self._api.get(
                metadata["links"]["requests"], params={"size": 10000}
            )["hits"]["hits"]

        return NRPRecord(
            client=self._api,
            model=model,
            record_id=record_id,
            data=metadata,
            files=files,
            requests=requests,
        )

    def create(self, model, metadata) -> NRPRecord:
        """
        Creates a new record in the repository

        :param model:       name of the model
        :param metadata:    metadata of the record, including the 'metadata' element
        :return:            The created record
        """
        response = self._api.post(
            self._api.info.get_model(model).links["api"], data=metadata
        )
        return NRPRecord(
            client=self._api, model=model, record_id=response["id"], data=response
        )


def _fetch_by_path(client, api_path, add_files, add_requests) -> NRPRecord:
    ret = client.get(api_path)
    files = None
    requests = None
    if add_files and "files" in ret["links"]:
        files = client.get(ret["links"]["files"])["entries"]
    if add_requests and "requests" in ret["links"]:
        requests = client.get(ret["links"]["requests"])["hits"]["hits"]
    model, id = get_mid(client.info.models, ret)
    return NRPRecord(
        client=client,
        model=model,
        record_id=id,
        data=ret,
        files=files,
        requests=requests,
    )


def record_getter(
    config: NRPConfig,
    record_id,
    include_files=False,
    include_requests=False,
    client=None,
) -> NRPRecord:
    """
    Gets a record, regardless of the format of the record id

    :param config:              The configuration of known repositories
    :param record_id:           if of the record in any supported formats (mid, doi, url)
    :param include_files:       If True, metadata the files of the record are fetched as well
    :param include_requests:    If True, the requests of the record are fetched as well included in the returned object.
    :param client:              Preferred client to use for fetching the record, if the id does not specify a concrete repository
    :return:                    The record
    """
    if is_doi(record_id):
        client_from_doi, api_path = resolve_record_doi(config, record_id)
        return _fetch_by_path(
            client_from_doi, api_path, include_files, include_requests
        )
    elif is_url(record_id):
        client_from_url, api_path = resolve_repository_url(config, record_id)
        return _fetch_by_path(
            client_from_url, api_path, include_files, include_requests
        )
    elif is_mid(record_id):
        if client is None:
            client = config.default_repository
        return client.records.get(
            mid=record_id,
            include_files=include_files,
            include_requests=include_requests,
        )
    else:
        raise ValueError(
            f"Unknown record id format for '{record_id}'. "
            "Pass either <model>/<id>, draft/<model>/<id>, API url, UI url or DOI"
        )
