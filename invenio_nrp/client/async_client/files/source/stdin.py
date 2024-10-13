import contextlib
from pathlib import Path
from typing import AsyncIterator

from .base import DataSource

from ..os import DataReader, file_stat, open_file


class StdInDataSource(DataSource):
    """A data source that reads data from standard input."""

    has_range_support = False

    # TODO: how to correctly type this?
    @contextlib.asynccontextmanager
    async def open(self, offset: int = 0) -> AsyncIterator[DataReader]: # type: ignore
        ret = await open_file(Path('/sys/stdin'), mode="rb")
        yield ret
        await ret.close()

    async def size(self) -> int:
        return -1

    async def content_type(self) -> str:
        return "application/octet-stream"

    async def close(self) -> None:
        """Closes the data source."""
        pass
