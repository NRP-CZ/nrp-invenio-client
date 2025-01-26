#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Bounded stream implementation."""

from typing import Any

from .base import InputStream


class BoundedStream:
    """A stream that reads a limited amount of data from another stream."""

    def __init__(self, stream: InputStream, limit: int):
        """Initialize the stream."""
        self._stream = stream
        self._remaining = limit

    async def read(self, size: int = -1) -> bytes:
        """Read data from the stream."""
        if self._remaining <= 0:
            return b""
        if size < 0:
            size = self._remaining
        data = await self._stream.read(min(size, self._remaining))
        self._remaining -= len(data)
        return data

    async def close(self) -> None:
        """Close the underlying stream."""
        await self._stream.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate all other calls to the underlying stream."""
        return getattr(self._stream, name)