#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Protocol for data sinks."""
from enum import StrEnum, auto
from typing import Protocol

from ..os import DataWriter


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

    async def allocate(self, size: int) -> None:
        """
        Allocate space for the sink.

        :param size: The size of the sink in bytes.
        """
        ...

    async def open_chunk(self, offset: int = 0) -> DataWriter:
        """
        Get a writer for the sink, starting at the given offset.

        :param offset: The offset in bytes from the start of the sink.
        :return: A writer for the sink.
        """
        ...

    async def close(self) -> None:
        """
        Close the sink and all unclosed writers.
        """
        ...

    @property
    def state(self) -> SinkState:
        """Return the current state of the sink."""
        ...
