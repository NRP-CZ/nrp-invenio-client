#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import asyncio
import time

from invenio_nrp.client.async_client.records import Record
from invenio_nrp.client.async_client.streams import MemorySource


async def test_create_many_files_in_parallel(draft_record_with_files: Record):
    files = draft_record_with_files.files()
    data = b"Hello world!"
    print()
    t1 = time.time()

    async with asyncio.TaskGroup() as tg:
        for fn in range(10):
            tg.create_task(
                files.upload(
                    key=f"blah_{fn}.txt",
                    metadata={"title": "blah"},
                    source=MemorySource(data, content_type="text/plain"),
                )
            )
    t2 = time.time()
    print(f"Time to upload 10 files in parallel: {(t2 - t1) * 1000} ms")

    listing = await files.list()
    assert len(listing.entries) == 10

    t1 = time.time()
    for fn in range(10):
        await files.upload(
            key=f"blah_{10+fn}.txt",
            metadata={"title": "blah"},
            source=MemorySource(data, content_type="text/plain"),
        )
    t2 = time.time()
    print(f"Time to upload 10 files sequentially: {(t2 - t1) * 1000} ms")

    listing = await files.list()
    assert len(listing.entries) == 20
