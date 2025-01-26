#
# This file was generated from the asynchronous client at streams/bounded_stream.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Bounded stream implementation."""

from typing import Any

from .base import InputStream


class BoundedStream(InputStream):
    """A stream that reads a limited amount of data from another stream."""

    def __init__(self, stream: InputStream, limit: int):
        """Initialize the stream."""
        self._stream = stream
        self._remaining = limit

    def read(self, size: int = -1) -> bytes:
        """Read data from the stream."""
        if self._remaining <= 0:
            return b""
        if size < 0:
            size = self._remaining
        data = self._stream.read(min(size, self._remaining))
        self._remaining -= len(data)
        return data

    def __len__(self) -> int:
        """Return the stream size."""
        return self.limit

    def close(self) -> None:
        """Close the underlying stream."""
        self._stream.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate all other calls to the underlying stream."""
        return getattr(self._stream, name)
    
    def __iter__(self):
         return self
    
    def __next__(self) -> bytes:
        return self.read(16384)
    
    
