#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of a sink that writes data to memory."""
import contextlib
from typing import AsyncIterator

from ..os import DataWriter
from .base import DataSink, SinkState
from .memory_writer import MemoryWriter


class MemorySink(DataSink):
    """Implementation of a sink that writes data to memory."""

    def __init__(self):
        self._state = SinkState.NOT_ALLOCATED
        self._buffer = None

    async def allocate(self, size: int) -> None:
        self._buffer = bytearray(size)
        self._state = SinkState.ALLOCATED

    @contextlib.asynccontextmanager
    async def open_chunk(self, offset: int = 0) -> AsyncIterator[DataWriter]:   # type: ignore
        if self._state != SinkState.ALLOCATED:
            raise RuntimeError("Sink not allocated")

        yield MemoryWriter(self._buffer, offset)  # noqa

    async def close(self) -> None:
        self._state = SinkState.CLOSED
