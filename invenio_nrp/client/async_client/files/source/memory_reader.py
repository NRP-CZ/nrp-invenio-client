#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Memory-based data source."""


class MemoryReader:
    """A reader for in-memory data."""

    def __init__(self, data: bytes):
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
