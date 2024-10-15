#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import pytest
import rich

from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.files import File
from invenio_nrp.client.async_client.records import Record
from invenio_nrp.client.async_client.request_types import RequestType
from invenio_nrp.client.async_client.requests import Request
from invenio_nrp.client.errors import RepositoryCommunicationError


async def test_publish_request_via_applicable(
    local_client, local_records, draft_record
):
    record_requests = draft_record.requests()
    applicable_requests = await record_requests.applicable()
    assert applicable_requests.keys() == {"publish_draft"}

    submitted_request = await applicable_requests.publish_draft.create({}, submit=True)
    assert submitted_request.status == "submitted"

    approved_request = await submitted_request.accept()
    assert approved_request.status == "accepted"

    published_record_link = approved_request.payload.published_record.links.self_
    published_record = await local_records.read_record(record_id=published_record_link)

    rich.print(published_record)
    assert published_record.state == "published"
    assert published_record.metadata["title"] == draft_record.metadata["title"]


async def test_delete_request(local_client, local_records, draft_record):
    applicable_requests = await draft_record.requests().applicable()

    publish_request = await applicable_requests.publish_draft.create({}, submit=True)
    published_request = await publish_request.accept()

    published_record_link = published_request.payload.published_record.links.self_
    published_record = await local_records.read_record(record_id=published_record_link)

    applicable_requests = await published_record.requests().applicable()

    delete_request = await applicable_requests.delete_published_record.create(
        {}, submit=True
    )
    deleted_request = await delete_request.accept()

    assert deleted_request.status == "accepted"

    with pytest.raises(RepositoryCommunicationError):
        await local_records.read_record(record_id=published_record_link)


async def test_list_requests(local_client: AsyncClient, draft_record):
    record_requests = draft_record.requests()
    all_requests = local_client.requests()

    # initial counts
    initially_submitted_requests_count = (await all_requests.submitted()).total
    initially_accepted_requests_count = (await all_requests.accepted()).total

    # create and submit new request
    applicable_requests = await record_requests.applicable()
    assert applicable_requests.keys() == {"publish_draft"}

    submitted_request = await applicable_requests.publish_draft.create({}, submit=True)
    assert submitted_request.status == "submitted"

    # make sure it is there
    requests = await all_requests.submitted()
    assert requests.total == 1 + initially_submitted_requests_count
    first_request = requests.hits[0]
    assert first_request.status == "submitted"
    assert first_request.id == submitted_request.id

    # look for it in all requests via all()
    async for req in requests.all():
        if req.id == submitted_request.id:
            break
    else:
        assert False, "Request not found in submitted requests"

    approved_request = await submitted_request.accept()
    assert approved_request.status == "accepted"

    requests = await all_requests.submitted()
    assert requests.total == initially_submitted_requests_count

    requests = await all_requests.accepted()
    assert requests.total == 1 + initially_accepted_requests_count

    # look for it here
    async for req in requests.all():
        if req.id == submitted_request.id:
            break
    else:
        assert False, "Request not found in accepted requests"
