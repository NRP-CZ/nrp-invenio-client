#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import pytest
from rich import print

from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.files import File
from invenio_nrp.client.async_client.records import Record
from invenio_nrp.client.async_client.request_types import RequestType
from invenio_nrp.client.async_client.requests import Request
from invenio_nrp.client.errors import RepositoryCommunicationError
from invenio_nrp.types import Model


async def test_create_record(local_client: AsyncClient):
    records_client = local_client.user_records()
    rec = await records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    assert isinstance(rec, Record)
    print(rec)
    assert rec.id is not None
    assert rec.metadata["title"] == "test"
    assert rec.parent["communities"]["default"] is not None


@pytest.mark.skip()
async def test_create_record_with_default_community(local_client: AsyncClient):
    records_client = local_client.user_records()
    rec = await records_client.create_record({"metadata": {"title": "test"}})
    assert isinstance(rec, Record)


async def test_get_record(local_client: AsyncClient):
    records_client = local_client.user_records()
    rec = await records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )

    # read the record given the pid
    rec2 = await records_client.read_record(record_id=rec.id)
    assert rec.metadata == rec2.metadata
    assert rec.id == rec2.id

    # read the record given the url
    rec3 = await records_client.read_record(record_url=rec.links.self_)
    assert rec.metadata == rec3.metadata
    assert rec.id == rec3.id

    # giving both should fail
    with pytest.raises(AssertionError):
        await records_client.read_record(record_id=rec.id, record_url=rec.links.self_)

    # giving none should fail
    with pytest.raises(AssertionError):
        await records_client.read_record()


async def test_remove_draft_record(local_client: AsyncClient):
    records_client = local_client.user_records()
    rec = await records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    rec2 = await records_client.read_record(record_id=rec.id)
    assert isinstance(rec2, Record)

    await rec2.delete()
    with pytest.raises(RepositoryCommunicationError):
        await records_client.read_record(record_id=rec.id)


async def test_update_draft_record(local_client: AsyncClient):
    records_client = local_client.user_records()
    rec = await records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    created_etag = rec._etag

    rec2 = await records_client.read_record(record_id=rec.id)
    read_etag = rec2._etag

    assert read_etag == created_etag

    # perform update
    rec2.metadata["title"] = "test2"
    rec3 = await rec2.update()

    updated_etag = rec3._etag
    assert read_etag != updated_etag

    rec4 = await records_client.read_record(record_id=rec.id)
    assert rec4.metadata["title"] == "test2"
    assert rec4._etag == updated_etag


async def test_read_all_records(local_client: AsyncClient):
    # create 30 records
    records_client = local_client.user_records()
    for i in range(30):
        await records_client.create_record(
            {"metadata": {"title": f"test{i}"}}, community="acom"
        )

    # read all records and check if they are at least 30, that is that pagination works
    fetched_records = []

    async for record in (
        await local_client.user_records().search(size=10, state="draft")
    ).all():
        fetched_records.append(record)

    print(f"Total fetched records: {len(fetched_records)}")
    assert len(fetched_records) >= 30

    for record in fetched_records:
        await record.delete()

    # now create controlled records
    created_records = []
    for i in range(10):
        created_records.append(
            await records_client.create_record(
                {"metadata": {"title": f"test{i}"}}, community="acom"
            )
        )

    # and search
    fetched_records = [
        x async for x in (await local_client.user_records().search(q="test1")).all()
    ]

    assert len(fetched_records) == 1
    f = fetched_records[0]
    assert f.metadata["title"] == "test1"

    # and clean up
    for record in created_records:
        await record.delete()


async def test_custom_record_class(nrp_repository_config):
    class MyMetadata(Model):
        title: str

    class MyRecord(Record):
        metadata: MyMetadata

    client = AsyncClient[MyRecord, File, Request, RequestType](
        alias="local", config=nrp_repository_config
    )
    await client.info()

    assert client._generic_arguments.RecordBase == MyRecord

    records_client = client.user_records
    rec = await records_client().create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    assert isinstance(rec, MyRecord)
    assert isinstance(rec.metadata, MyMetadata)
    assert rec.metadata.title == "test"

    rec2 = await records_client().read_record(record_id=rec.id)
    assert isinstance(rec2, MyRecord)
    assert isinstance(rec2.metadata, MyMetadata)
    assert rec2.metadata.title == "test"

    reclist = await records_client().search(size=1)
    assert len(reclist) == 1
    assert isinstance(reclist.hits[0], MyRecord)
    assert isinstance(reclist.hits[0].metadata, MyMetadata)