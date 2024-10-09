#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Low-level compatibility layer for file operations."""
import os
from pathlib import Path

import aiofiles
import aiofiles.os
from aiofiles.threadpool.binary import AsyncBufferedIOBase, AsyncBufferedReader

type DataReader = AsyncBufferedReader
"""Type alias for the data reader."""

type DataWriter = AsyncBufferedIOBase
"""Type alias for the data writer."""


async def open_file(_fpath: Path, mode: str) -> DataReader | DataWriter:
    """Open a file for reading or writing."""
    r: DataReader | DataWriter = await aiofiles.open(_fpath, mode=mode)  # noqa
    return r


async def file_stat(_fpath: Path) -> os.stat_result:
    """Get file statistics."""
    return await aiofiles.os.stat(_fpath)


__all__ = (
    "DataReader",
    "DataWriter",
    "open_file",
    "file_stat",
)
