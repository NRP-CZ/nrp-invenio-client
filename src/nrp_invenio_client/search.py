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
    """
    Search request builder. It allows to build a search query and execute it.
    Do not instantiate this class directly, use `NRPInvenioClient.search` method instead.
    """

    def __init__(self, api: "NRPInvenioClient", models=None):
        self._api = api
        self._models = models
        self._query = None
        self._params = {}
        self._url_selector: UrlSelector = UrlSelector.PUBLISHED

    def execute(self) -> "NRPSearchResponse":
        """
        Executes the search query and returns the response.
        """
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
        """
        Executes the search query in the scan mode, allowing to return more
        than 10000 records. The result of this call must be used as a context manager,
        for example:

        query = ...
        with query.scan() as results:
            for record in results:
                ...
        """
        return NRPScanResponse(self, self._get_path(method="scan"), self.models)

    def page(self, page: int):
        """
        Fetch the specified page of results.
        :param page:    page number, starting with 1
        """
        if page:
            self._params["page"] = page
        else:
            self._params.pop("page", None)
        return self

    def size(self, size: int):
        """
        The fetched pages will have this number of records.
        :param size:    number of records per page
        """
        if size:
            self._params["size"] = size
        else:
            self._params.pop("size", None)
        return self

    def order_by(self, *sort: str):
        """
        Sort the results by the specified fields.

        :param sort:    fields to sort by. A field can have a '+/-' prefix to specify the sort order.
        """
        if len(sort) == 0:
            self._params.pop("sort", None)
            return self
        self._params["sort"] = ",".join(sort)
        return self

    def published(self):
        """
        Return only published records
        """
        self._url_selector = UrlSelector.PUBLISHED
        return self

    def drafts(self):
        """
        Return only draft records
        """
        self._url_selector = UrlSelector.DRAFTS
        return self

    def query(self, query):
        """
        Set the search query. The query can be either a SOLR/Opensearch query string or a JSON query.
        """
        self._query = query
        return self

    # TODO: paths here are not correct, should be present inside the info endpoint and not created here
    def _get_path(self, method="search"):
        """
        Internal method to get the search path
        """
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
        """
        Models that will be searched within the query
        """
        if self._models:
            return [x for x in self._api.info.models if x.name in self._models]
        else:
            return self._api.info.models


class NRPSearchBaseResponse:
    """
    Base class for search/scan responses
    """

    def __init__(self, api, models: typing.List[NRPModelInfo]):
        self._api = api
        self._models = models


class NRPSearchResponse(NRPSearchBaseResponse):
    """
    Search response. It is an iterable of NRPRecord objects.
    This class is not intended to be instantiated directly, use `NRPSearchRequest.execute` method instead.
    """

    def __init__(self, api, raw_response, models):
        super().__init__(api, models)
        self._raw_response = raw_response

    def __iter__(self) -> typing.Iterator[NRPRecord]:
        """
        Iterate over the records
        """
        for hit_data in self._raw_response["hits"]["hits"]:
            (model, record_id) = get_mid(self._models, hit_data)
            yield NRPRecord(
                client=self._api, data=hit_data, model=model, record_id=record_id
            )

    @property
    def links(self):
        """
        Return the links section of the response, such as `next` or `prev` page.
        """
        return self._raw_response["links"]

    @property
    def total(self):
        """
        Total number of found records
        """
        total = self._raw_response["hits"]["total"]
        if isinstance(total, int):
            return total
        if "value" in total:
            return total["value"]
        return None


class NRPScanResponse(NRPSearchBaseResponse):
    """
    Scan response. It is an iterable of NRPRecord objects but has to be used
    as a context manager as it needs to be closed after the iteration.

    Unlike search response, it does not return the total number of records
    nor pagination links.
    """

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
        """
        Iterate over the records
        """
        while self._url:
            # get next batch of results
            response = self._api.get(self._url)
            for hit_data in response["hits"]["hits"]:
                (model, record_id) = get_mid(self._models, hit_data)
                yield NRPRecord(
                    client=self._api, data=hit_data, model=model, record_id=record_id
                )
            self._url = response.get("links", {}).get("next", None)
