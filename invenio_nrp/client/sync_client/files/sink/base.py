#
# This file was generated from the asynchronous client at files/sink/base.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Protocol for data sinks."""
import contextlib
from enum import StrEnum, auto
from typing import Protocol

from ..os import DataWriter
from typing import ContextManager


class SinkState(StrEnum):
    """State of the sink."""

    NOT_ALLOCATED = auto()
    """Sink's space has not been allocated yet."""
    ALLOCATED = auto()
    """Sink's space has been allocated and reserved on the filesystem/memory."""
    CLOSED = auto()
    """Sink has been closed."""


class DataSink(Protocol):
    """Protocol for data sinks."""

    def allocate(self, size: int) -> None:
        """Allocate space for the sink.

        :param size: The size of the sink in bytes.
        """
        ...

    def open_chunk(self, offset: int = 0) -> ContextManager[DataWriter]:
        """Get a writer for the sink, starting at the given offset.

        :param offset: The offset in bytes from the start of the sink.
        :return: A writer for the sink.
        """
        ...

    def close(self) -> None:
        """Close the sink and all unclosed writers."""
        ...

    @property
    def state(self) -> SinkState:
        """Return the current state of the sink."""
        ...
