from invenio_nrp.client.async_client.records import RecordList
from invenio_nrp.converter import converter


def test_record_list():
    data = {
        "hits": {
            "total": 100,
            "hits": [
                {
                    "metadata": {"title": "test1"},
                    "links": {"self": "http://localhost:5000/api/records/1"},
                    "created": "2021-01-01T00:00:00Z",
                    "updated": "2021-01-01T00:00:00Z",
                    "id": "1",
                },
            ],
        },
        "aggregations": {},
        "links": {
            "self": "http://localhost:5000/api/records",
        },
    }
    output = converter.structure(data, RecordList)
