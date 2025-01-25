#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from io import BytesIO
from struct import pack

import pytest

from invenio_nrp.client.async_client.files import File, FilesClient, TransferType
from invenio_nrp.client.async_client.files.source.memory import MemoryDataSource
from invenio_nrp.client.async_client.records import Record


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


@pytest.mark.parametrize("data_size,parts", [(20, 5), (100, 20), (10, 10)])
async def test_multipart_upload(draft_record_with_files: Record, data_size, parts):
    # generate 20MB of data, filled with 8bytes as an address
    print(f"Generating {data_size}MB of data")
    io = BytesIO()
    for i in range(data_size * 1024 * 1024 // 8):
        io.write(pack(">Q", i))

    print(f"Uploading {data_size}MB of data in {parts} chunks")
    files: FilesClient = draft_record_with_files.files()

    committed_upload: File = await files.upload(
        key="blah.txt",
        metadata={"title": "blah"},
        file=MemoryDataSource(io.getvalue(), content_type="text/plain"),
        transfer_type=TransferType.MULTIPART,
        transfer_metadata={"parts": parts},
    )

    print(committed_upload)
    assert committed_upload.links.content is not None
    assert committed_upload.status == "completed"
    assert committed_upload.metadata["title"] == "blah"
    assert committed_upload.size == data_size * 1024 * 1024

    assert committed_upload.transfer.type_ == "L"

    # read the file back
    print("Downloading the file back")
    async with committed_upload._connection.get_stream(
        url=committed_upload.links.content
    ) as stream:
        data = await stream.read()
        assert data == io.getvalue()