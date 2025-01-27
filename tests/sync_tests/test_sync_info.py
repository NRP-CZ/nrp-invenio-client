#
# This file was generated from the asynchronous client at test_async_info.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


from yarl import URL


def test_sync_info(local_client):
    info = local_client.info(refresh=True)
    _check_info(info)


def _check_info(info):
    assert info.version == "local development"
    assert info.links.self_ == URL("https://127.0.0.1:5000/.well-known/repository/")
    assert info.links.models == URL(
        "https://127.0.0.1:5000/.well-known/repository/models"
    )
    model = info.models["simple"]
    assert model.name == "simple"
    assert model.version == "1.0.0"
    assert model.links.api == URL("https://127.0.0.1:5000/api/simple/")
    assert model.links.published == URL("https://127.0.0.1:5000/api/simple/")
    assert model.links.user_records == URL("https://127.0.0.1:5000/api/user/simple/")


def test_sync_info_zenodo(zenodo_client):
    info = zenodo_client.info()

    assert info.version == "rdm"
    assert info.links.self_ == URL("https://www.zenodo.org")
    assert info.links.models is None
    assert info.links.records == URL("https://www.zenodo.org/api/records/")
    assert info.links.user_records == URL("https://www.zenodo.org/api/user/records/")

