#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Memory-based data source."""

import contextlib
from typing import AsyncIterator

from ..os import DataReader
from .base import DataSource
from .memory_reader import MemoryReader


class MemoryDataSource(DataSource):
    """A data source that reads data from memory."""

    has_range_support = True

    def __init__(self, data: bytes, content_type: str):
        """Initialize the data source.

        :param data:                the data to be read
        :param content_type:        the content type of the data
        """
        self._data = data
        self._content_type = content_type

    # TODO: how to correctly type this?
    @contextlib.asynccontextmanager
    async def open(self, offset: int = 0) -> AsyncIterator[DataReader]:  # type: ignore
        """Open the data source for reading."""
        yield MemoryReader(self._data[offset:])  # noqa ignore type

    async def size(self) -> int:
        """Return the size of the data."""
        return len(self._data)

    async def content_type(self) -> str:
        """Return the content type of the data."""
        return self._content_type

    async def close(self) -> None:
        """Close the data source."""
        pass
