#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of a sink that writes data to memory."""

from ..os import DataWriter
from .base import DataSink, SinkState


class MemoryWriter:
    """Implementation of a writer that writes data to memory."""

    def __init__(self, buffer: bytearray, offset: int):
        """Initialize the writer.

        :param buffer: The buffer where the data will be written.
        :param offset: The offset in bytes from the start of the buffer.
        """
        self._buffer = buffer
        self._offset = offset

    async def write(self, b: bytes) -> int:
        """
        Write data to the buffer.

        :param b: the bytes to be written
        :return:  number of bytes written
        """
        self._buffer[self._offset : self._offset + len(b)] = b
        self._offset += len(b)
        return len(b)

    async def close(self):
        pass


class MemorySink(DataSink):
    """Implementation of a sink that writes data to memory."""

    def __init__(self):
        self._state = SinkState.NOT_ALLOCATED
        self._buffer = None

    async def allocate(self, size: int) -> None:
        self._buffer = bytearray(size)
        self._state = SinkState.ALLOCATED

    async def open_chunk(self, offset: int = 0) -> DataWriter:
        if self._state != SinkState.ALLOCATED:
            raise RuntimeError("Sink not allocated")

        return MemoryWriter(self._buffer, offset)  # noqa

    async def close(self) -> None:
        self._state = SinkState.CLOSED
