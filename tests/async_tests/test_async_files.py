#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from invenio_nrp.client.async_client.files import File
from invenio_nrp.client.async_client.files.source.memory import MemoryDataSource
from invenio_nrp.client.async_client.records import Record
from invenio_nrp.client.async_client.request_types import RequestType
from invenio_nrp.client.async_client.requests import Request


async def test_list_files(draft_record: Record, draft_record_with_files: Record):
    files = draft_record.files()
    listing = await files.list()
    assert listing.enabled == False
    assert listing.entries == []
    assert listing.links.self_ is not None

    files = draft_record_with_files.files()
    listing = await files.list()
    assert listing.enabled == True
    assert listing.entries == []

    data = b"Hello world!"
    committed_upload = await files.upload(
        key="blah.txt",
        metadata={"title": "blah"},
        file=MemoryDataSource(data, content_type="text/plain"),
    )

    print(committed_upload)
    assert committed_upload.links.content is not None
    assert committed_upload.status == "completed"
    assert committed_upload.metadata["title"] == "blah"
    assert committed_upload.size == len(data)
    assert committed_upload.checksum is not None

    listing = await files.list()
    assert listing.enabled == True
    assert len(listing.entries) == 1
    assert listing.entries[0].key == "blah.txt"
