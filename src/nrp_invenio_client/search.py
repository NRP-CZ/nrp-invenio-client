import typing
from enum import Enum

from .info import NRPModelInfo
from .records import NRPRecord
from .utils import get_mid

if typing.TYPE_CHECKING:
    from nrp_invenio_client.base import NRPInvenioClient


class UrlSelector(Enum):
    PUBLISHED = "published"
    DRAFTS = "drafts"


class NRPSearchRequest:
    def __init__(self, api: "NRPInvenioClient", models=None):
        self._api = api
        self._models = models
        self._query = None
        self._params = {}
        self._url_selector: UrlSelector = UrlSelector.PUBLISHED

    def execute(self):
        if self._query:
            if isinstance(self._query, str):
                p = {"q": self._query, **self._params}
            else:
                p = {"json": self._query, **self._params}
        else:
            p = self._params
        return NRPSearchResponse(
            self._api,
            self._api.get(path=self._get_path(method="search"), params=p),
            self.models,
        )
        # TODO: json query with POST method (if the query is too long)

    def scan(self):
        return NRPScanResponse(self, self._get_path(method="scan"), self.models)

    def page(self, page: int):
        if page:
            self._params["page"] = page
        else:
            self._params.pop("page", None)
        return self

    def size(self, size: int):
        if size:
            self._params["size"] = size
        else:
            self._params.pop("size", None)
        return self

    def order_by(self, *sort: str):
        if len(sort) == 0:
            self._params.pop("sort", None)
            return self
        self._params["sort"] = ",".join(sort)
        return self

    def published(self):
        self._url_selector = UrlSelector.PUBLISHED
        return self

    def drafts(self):
        self._url_selector = UrlSelector.DRAFTS
        return self

    def query(self, query):
        self._query = query
        return self

    # TODO: paths here are not correct, should be present inside the info endpoint and not created here
    def _get_path(self, method="search"):
        suffix = "" if method == "search" else "/_scan"
        if len(self._models) == 1:
            model_info = self._api.info.get_model(self._models[0])
            match self._url_selector:
                case UrlSelector.PUBLISHED:
                    return model_info.links["published"] + suffix
                case UrlSelector.DRAFTS:
                    return model_info.links["drafts"] + suffix

        match self._url_selector:
            case UrlSelector.PUBLISHED:
                return "/api/search" + suffix
            case UrlSelector.DRAFTS:
                return "/api/user/search" + suffix

    @property
    def models(self):
        if self._models:
            return [x for x in self._api.info.models if x.name in self._models]
        else:
            return self._api.info.models


class NRPSearchBaseResponse:
    def __init__(self, api, models: typing.List[NRPModelInfo]):
        self._api = api
        self._models = models


class NRPSearchResponse(NRPSearchBaseResponse):
    def __init__(self, api, raw_response, models):
        super().__init__(api, models)
        self._raw_response = raw_response

    def __iter__(self) -> typing.Iterator[NRPRecord]:
        for hit_data in self._raw_response["hits"]["hits"]:
            (model, record_id) = get_mid(self._models, hit_data)
            yield NRPRecord(
                client=self._api, data=hit_data, model=model, record_id=record_id
            )

    @property
    def links(self):
        return self._raw_response["links"]

    @property
    def total(self):
        total = self._raw_response["hits"]["total"]
        if isinstance(total, int):
            return total
        if "value" in total:
            return total["value"]
        return None


class NRPScanResponse(NRPSearchBaseResponse):
    def __init__(self, api, url, models):
        super().__init__(api, models)
        self._url = url

    def __enter__(self):
        # initiate the scanning
        self._url = self._api.post(self._url)["links"]["self"]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # finish the scanning
        self._api.delete(self._url)

    def __iter__(self) -> typing.Iterator[NRPRecord]:
        while self._url:
            # get next batch of results
            response = self._api.get(self._url)
            for hit_data in response["hits"]["hits"]:
                (model, record_id) = get_mid(self._models, hit_data)
                yield NRPRecord(
                    client=self._api, data=hit_data, model=model, record_id=record_id
                )
            self._url = response.get("links", {}).get("next", None)
