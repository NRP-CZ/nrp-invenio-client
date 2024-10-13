#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#

#
# This file was generated from the asynchronous client at test_async_requests.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import pytest
import rich

from invenio_nrp.client import SyncClient
from invenio_nrp.client.errors import RepositoryCommunicationError
from invenio_nrp.client.sync_client.files import File
from invenio_nrp.client.sync_client.records import Record
from invenio_nrp.client.sync_client.request_types import RequestType
from invenio_nrp.client.sync_client.requests import Request


def test_publish_request_via_applicable(local_client, local_records, draft_record):
    record_requests = draft_record.requests()
    applicable_requests = record_requests.applicable()
    assert applicable_requests.keys() == {"publish_draft"}

    submitted_request = applicable_requests.publish_draft.create({}, submit=True)
    assert submitted_request.status == "submitted"

    approved_request = submitted_request.accept()
    assert approved_request.status == "accepted"

    published_record_link = approved_request.payload.published_record.links.self_
    published_record = local_records.read_record(record_url=published_record_link)

    rich.print(published_record)
    assert published_record.state == "published"
    assert published_record.metadata["title"] == draft_record.metadata["title"]


def test_delete_request(local_client, local_records, draft_record):
    applicable_requests = draft_record.requests().applicable()

    publish_request = applicable_requests.publish_draft.create({}, submit=True)
    published_request = publish_request.accept()

    published_record_link = published_request.payload.published_record.links.self_
    published_record = local_records.read_record(record_url=published_record_link)

    applicable_requests = published_record.requests().applicable()

    delete_request = applicable_requests.delete_published_record.create({}, submit=True)
    deleted_request = delete_request.accept()

    assert deleted_request.status == "accepted"

    with pytest.raises(RepositoryCommunicationError):
        local_records.read_record(record_url=published_record_link)


def test_list_requests(local_client: SyncClient, draft_record):
    record_requests = draft_record.requests()
    all_requests = local_client.requests()

    # initial counts
    initially_submitted_requests_count = (all_requests.submitted()).total
    initially_accepted_requests_count = (all_requests.accepted()).total

    # create and submit new request
    applicable_requests = record_requests.applicable()
    assert applicable_requests.keys() == {"publish_draft"}

    submitted_request = applicable_requests.publish_draft.create({}, submit=True)
    assert submitted_request.status == "submitted"

    # make sure it is there
    requests = all_requests.submitted()
    assert requests.total == 1 + initially_submitted_requests_count
    first_request = requests.hits[0]
    assert first_request.status == "submitted"
    assert first_request.id == submitted_request.id

    # look for it in all requests via all()
    for req in requests.all():
        if req.id == submitted_request.id:
            break
    else:
        assert False, "Request not found in submitted requests"

    approved_request = submitted_request.accept()
    assert approved_request.status == "accepted"

    requests = all_requests.submitted()
    assert requests.total == initially_submitted_requests_count

    requests = all_requests.accepted()
    assert requests.total == 1 + initially_accepted_requests_count

    # look for it here
    for req in requests.all():
        if req.id == submitted_request.id:
            break
    else:
        assert False, "Request not found in accepted requests"


def test_custom_request_class(nrp_repository_config):
    class MyRequest(Request):
        pass

    MyRecord = Record[File, MyRequest, RequestType[MyRequest]]

    client = SyncClient[MyRecord, File, MyRequest, RequestType[MyRequest]](
        alias="local", config=nrp_repository_config
    )
    client.info()

    records_client = client.user_records()
    rec = records_client.create_record(
        {"metadata": {"title": "test"}}, community="acom"
    )
    record_requests = rec.requests()

    # create and submit new request
    applicable_requests = record_requests.applicable()
    assert applicable_requests.keys() == {"publish_draft"}

    submitted_request = applicable_requests.publish_draft.create({}, submit=True)
    assert isinstance(submitted_request, MyRequest)

    global_requests = client.requests()

    for req in global_requests.all():
        assert isinstance(req, MyRequest)
