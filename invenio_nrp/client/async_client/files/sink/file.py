#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Implementation of a sink that writes data to filesystem."""

import contextlib
from pathlib import Path
from typing import AsyncIterator

from ..os import DataWriter, open_file
from .base import DataSink, SinkState


class FileSink(DataSink):
    """Implementation of a sink that writes data to filesystem."""

    def __init__(self, fpath: Path):
        """Initialize the sink.

        :param fpath: The path to the file where the data will be written.
        """
        self._fpath = fpath
        self._state = SinkState.NOT_ALLOCATED
        self._file: DataWriter | None = None

    async def allocate(self, size: int) -> None:
        """Allocate space for the sink."""
        self._file = await open_file(self._fpath, mode="wb")
        await self._file.truncate(size)
        self._state = SinkState.ALLOCATED

    @contextlib.asynccontextmanager
    async def open_chunk(self, offset: int = 0) -> AsyncIterator[DataWriter]:  # type: ignore
        """Open a chunk of the sink for writing."""
        if self._state != SinkState.ALLOCATED:
            raise RuntimeError("Sink not allocated")

        chunk = await open_file(self._fpath, mode="r+b")
        await chunk.seek(offset)
        yield chunk
        await chunk.close()

    async def close(self) -> None:
        """Close the sink."""
        if self._file is not None:
            with contextlib.suppress(Exception):
                await self._file.close()
        self._file = None

        self._state = SinkState.CLOSED

    @property
    def state(self) -> SinkState:
        """Return the current state of the sink."""
        return self._state

    def __repr__(self):
        """Return a string representation of the sink."""
        return f"<{self.__class__.__name__} {self._fpath} {self._state}>"
