#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""File data source"""
import contextlib
from pathlib import Path
from typing import AsyncIterator

import magic

from ..os import DataReader, file_stat, open_file
from .base import DataSource


class FileDataSource(DataSource):
    """A data source that reads data from a file."""

    has_range_support = True

    def __init__(self, file_name: Path | str):
        """Initialize the data source.

        :param file_name: The name of the file to read from, must exist on the filesystem
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        self._file_name = file_name

    # TODO: how to correctly type this?
    @contextlib.asynccontextmanager
    async def open(self, offset: int = 0) -> AsyncIterator[DataReader]:  # type: ignore
        ret = await open_file(self._file_name, mode="rb")
        await ret.seek(offset)
        yield ret
        await ret.close()

    async def size(self) -> int:
        return (await file_stat(self._file_name)).st_size

    async def content_type(self) -> str:
        f = await open_file(self._file_name, mode="rb")
        try:
            data = await f.read(2048)
            return magic.from_buffer(data, mime=True)
        finally:
            await f.close()

    async def close(self) -> None:
        pass
