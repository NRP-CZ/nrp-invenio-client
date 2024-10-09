#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import sys
from pathlib import Path

from invenio_nrp.cli.records.metadata import read_metadata


async def upload_files_to_record(record, files):
    # convert files to pairs
    files = zip(files[::2], files[1::2])
    for file, metadata in files:
        metadata = read_metadata(metadata)
        if file == "-":
            file = sys.stdin.buffer
            key = metadata.get("key", "stdin")
        else:
            key = metadata.get("key", Path(file).name)
        # TODO: more efficient transfer of large/number of files in parallel here
        await record.files().upload(
            key,
            metadata,
            file,
        )
