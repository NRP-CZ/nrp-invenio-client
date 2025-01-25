#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Data source that reads data from standard input."""

import contextlib
from pathlib import Path
from typing import AsyncIterator

from ..os import DataReader, open_file
from .base import DataSource


class StdInDataSource(DataSource):
    """A data source that reads data from standard input."""

    has_range_support = False

    # TODO: how to correctly type this?
    @contextlib.asynccontextmanager
    async def open(self, offset: int = 0, count: int | None = None) -> AsyncIterator[DataReader]:  # type: ignore
        """Open the data source for reading."""
        if count is not None:
            raise ValueError("Cannot read a bounded stream from standard input.")
        if offset != 0:
            raise ValueError("Cannot seek in standard input.")
        ret = await open_file(Path("/sys/stdin"), mode="rb")
        yield ret
        await ret.close()

    async def size(self) -> int:
        """Return the size of the data - in this case -1 as unknown."""
        return -1

    async def content_type(self) -> str:
        """Return the content type of the data."""
        return "application/octet-stream"

    async def close(self) -> None:
        """Close the data source."""
        pass
