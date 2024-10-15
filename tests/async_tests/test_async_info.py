#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from yarl import URL


async def test_async_info(local_client):
    info = await local_client.info()
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


async def test_async_info_zenodo(zenodo_client):
    info = await zenodo_client.info()

    assert info.version == "unknown"
    assert info.links.self_ is None
    assert info.links.models is None
    assert info.links.records == URL("https://www.zenodo.org/api/records/")
    assert info.links.user_records == URL("https://www.zenodo.org/api/user/records/")
