#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import pytest

from invenio_nrp.client import AsyncClient


@pytest.fixture()
async def local_client(nrp_repository_config):
    ret = AsyncClient(alias="local", config=nrp_repository_config)
    await ret.info()
    return ret


@pytest.fixture()
async def zenodo_client(nrp_repository_config):
    ret = AsyncClient(alias="zenodo", config=nrp_repository_config)
    await ret.info()
    return ret


@pytest.fixture(scope="function")
def local_records(local_client):
    return local_client.user_records()


@pytest.fixture(scope="function")
async def draft_record(request, local_client):
    records_client = local_client.user_records
    return await records_client().create_record(
        {
            "metadata": {"title": f"async draft record for {request.node.name}"},
            "files": {"enabled": False},
        },
        community="acom",
        files_enabled=False,
    )


@pytest.fixture(scope="function")
async def draft_record_with_files(request, local_client):
    records_client = local_client.user_records
    return await records_client().create_record(
        {
            "metadata": {"title": f"async draft record for {request.node.name}"},
        },
        community="acom",
        files_enabled=True,
    )
