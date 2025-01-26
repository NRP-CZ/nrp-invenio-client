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
from typing import Literal, overload

import aiofiles
import aiofiles.os

from .base import InputStream, OutputStream


class FileInputStream(InputStream):
    async def seek(self, offset: int, whence: int = os.SEEK_SET) -> None:
        """Change the stream position."""
        ...
        
class FileOutputStream(OutputStream):
    async def seek(self, offset: int, whence: int = os.SEEK_SET) -> None:
        """Change the stream position."""
        ...

    async def truncate(self, size: int) -> None:
        ...
        
@overload
async def open_file(_fpath: Path, mode: Literal["rb"]) -> FileInputStream:
    ...

@overload
async def open_file(_fpath: Path, mode: Literal["wb"] | Literal["r+b"]) -> FileOutputStream:
    ...

async def open_file(_fpath: Path, mode: Literal["rb"] | Literal["wb"] | Literal["r+b"]) -> FileInputStream | FileOutputStream:
    """Open a file for reading or writing."""
    r: FileInputStream | FileOutputStream = await aiofiles.open(_fpath, mode=mode)  # noqa # type: ignore
    return r


async def file_stat(_fpath: Path) -> os.stat_result:
    """Get file statistics."""
    return await aiofiles.os.stat(_fpath)


__all__ = (
    "open_file",
    "file_stat",
    "FileInputStream",
    "FileOutputStream",
)
