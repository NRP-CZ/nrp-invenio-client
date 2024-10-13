#
# This file was generated from the asynchronous client at files/sink/memory.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Implementation of a sink that writes data to memory."""
import contextlib
from typing import Iterator

from ..os import DataWriter
from .base import DataSink, SinkState
from .memory_writer import MemoryWriter


class MemorySink(DataSink):
    """Implementation of a sink that writes data to memory."""

    def __init__(self):
        self._state = SinkState.NOT_ALLOCATED
        self._buffer = None

    def allocate(self, size: int) -> None:
        self._buffer = bytearray(size)
        self._state = SinkState.ALLOCATED

    @contextlib.contextmanager
    def open_chunk(self, offset: int = 0) -> Iterator[DataWriter]:   # type: ignore
        if self._state != SinkState.ALLOCATED:
            raise RuntimeError("Sink not allocated")

        yield MemoryWriter(self._buffer, offset)  # noqa

    def close(self) -> None:
        self._state = SinkState.CLOSED
