#
# This file was generated from the asynchronous client at test_async_crud.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


import pytest
from rich import print

from invenio_nrp.client import SyncClient
from invenio_nrp.client.sync_client.records import Record
from invenio_nrp.client.errors import RepositoryCommunicationError


def test_create_record(local_client: SyncClient):
    records_client = local_client.user_records(model="simple")
    rec = records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    assert isinstance(rec, Record)
    print(rec)
    assert rec.id is not None
    assert rec.metadata and rec.metadata["title"] == "test"
    assert rec.parent and rec.parent.communities["default"] is not None


@pytest.mark.skip()
def test_create_record_with_default_community(local_client: SyncClient):
    records_client = local_client.user_records()
    rec = records_client.create_record({"metadata": {"title": "test"}})
    assert isinstance(rec, Record)


def test_get_record(local_client: SyncClient):
    records_client = local_client.user_records()
    rec = records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )

    # read the record given the pid
    rec2 = records_client.read_record(record_id=rec.id)
    assert rec.metadata == rec2.metadata
    assert rec.id == rec2.id

    # read the record given the url
    rec3 = records_client.read_record(record_id=rec.links.self_)
    assert rec.metadata == rec3.metadata
    assert rec.id == rec3.id

    # giving none should fail
    with pytest.raises(TypeError):
        records_client.read_record()


def test_remove_draft_record(local_client: SyncClient):
    records_client = local_client.user_records()
    rec = records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    rec2 = records_client.read_record(record_id=rec.id)
    assert isinstance(rec2, Record)

    rec2.delete()
    with pytest.raises(RepositoryCommunicationError):
        records_client.read_record(record_id=rec.id)


def test_update_draft_record(local_client: SyncClient):
    records_client = local_client.user_records()
    rec = records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    created_etag = rec._etag

    rec2 = records_client.read_record(record_id=rec.id)
    read_etag = rec2._etag

    assert read_etag == created_etag

    # perform update
    rec2.metadata["title"] = "test2"
    rec3 = rec2.update()

    updated_etag = rec3._etag
    assert read_etag != updated_etag

    rec4 = records_client.read_record(record_id=rec.id)
    assert rec4.metadata["title"] == "test2"
    assert rec4._etag == updated_etag


def test_read_all_records(local_client: SyncClient):
    # create 30 records
    records_client = local_client.user_records()

    # remove all records that might have been left from previous tests
    fetched_records = []
    for record in (
        local_client.user_records().search(size=100, state="draft")
    ).all():
        fetched_records.append(record)

    print(f"Total fetched records left from previous tests: {len(fetched_records)}")

    for record in fetched_records:
        record.delete()

    # create a bunch of records
    for i in range(30):
        records_client.create_record(
            {"metadata": {"title": f"test{1000+i}"}}, community="acom"
        )

    # read all records and check if they are at least 30, that is that pagination works
    fetched_records = []

    for record in (
        local_client.user_records().search(size=10, state="draft")
    ).all():
        fetched_records.append(record)

    print(f"Total fetched records: {len(fetched_records)}")
    assert len(fetched_records) >= 30

    # now create controlled records
    created_records = []
    for i in range(10):
        created_records.append(
            records_client.create_record(
                {"metadata": {"title": f"test{i}"}}, community="acom"
            )
        )

    # and search
    fetched_records = [
        x for x in (local_client.user_records().search(q="test1")).all()
    ]

    assert len(fetched_records) == 1
    f = fetched_records[0]
    assert f.metadata["title"] == "test1"

    # and clean up
    for record in created_records:
        record.delete()

