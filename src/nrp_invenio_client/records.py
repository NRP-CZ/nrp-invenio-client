import typing
from urllib.parse import urljoin

from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.files import NRPFile, NRPRecordFiles
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
        self._requests = requests

    @property
    def data(self):
        return self._data

    def to_dict(self):
        ret = {
            "mid": self.record_id,
            **self._data,
        }
        if self._files:
            ret["files"] = self._files.to_dict()
        if self._requests:
            ret["requests"] = self._requests
        return ret

    @property
    def metadata(self):
        if not self.data:
            return {}
        return self._data.get("metadata", None) or self._data

    @property
    def files(self):
        return self._files

    @property
    def requests(self):
        return self._requests

    @property
    def links(self):
        return self._data["links"]

    @property
    def record_id(self):
        if self.links.get('self') == self.links.get('draft'):
            return f"draft/{self._model}/{self._record_id}"
        else:
            return f"{self._model}/{self._record_id}"

    def clear_data(self):
        for k in list(self._data.keys()):
            if k not in ('links', 'parent', 'revision_id', 'id'):
                del self._data[k]

    def save(self):
        ret = self._client.put(
            self.links["self"], data=self.to_dict(),
            headers={"Content-Type": "application/json",
                     "If-Match": str(self._data["revision_id"])}
        )
        self._data = ret

    def delete(self):
        return self._client.delete(
            self.links["self"],
            headers={}
        )

    def publish(self):
        raise NotImplementedError()

    def edit(self):
        raise NotImplementedError()

    def __str__(self):
        return f"NRPRecord[{self._model}/{self._record_id}]"


class NRPRecordsApi:
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

    def create(self, model, metadata):
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
    config: NRPConfig, record_id, include_files=False, include_requests=False, client=None
) -> NRPRecord:
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
