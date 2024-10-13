#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Memory-based data source."""

from ..os import DataReader
from .base import DataSource


class MemoryReader:
    """A reader for in-memory data."""

    def __init__(self, data):
        """Initialize the reader.

        :param data:        the data that will be read
        """
        self._data = data

    def __aiter__(self):
        """We are our own iterator."""
        return self

    async def __anext__(self):
        """Simulate normal file iteration."""
        if self._data:
            ret = self._data
            self._data = None
            return ret
        else:
            raise StopAsyncIteration


class MemoryDataSource(DataSource):
    """A data source that reads data from memory."""

    def __init__(self, data: bytes, content_type: str):
        """Initialize the data source.

        :param data:                the data to be read
        :param content_type:        the content type of the data
        """
        self._data = data
        self._content_type = content_type

    async def open(self, offset: int = 0) -> DataReader:
        return MemoryReader(self._data[offset:])  # noqa ignore type

    async def size(self) -> int:
        return len(self._data)

    async def content_type(self) -> str:
        return self._content_type

    async def close(self) -> None:
        pass
