from invenio_nrp.client.async_client.files.files import File, FileLinks
from invenio_nrp.converter import converter


def test_file_structuring():
    data = {
        "key": "blah.txt",
        "links": {
            "self": "http://localhost:5000/api/files/1",
            "content": "http://localhost:5000/api/files/1/content",
        }
    }
    output = converter.structure(data, File)
    assert isinstance(output.links, FileLinks)