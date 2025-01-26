#
# This file was generated from the asynchronous client at streams/file.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""File sources and sinks."""

import contextlib
from pathlib import Path

import magic

from .base import DataSink, DataSource, InputStream, OutputStream, SinkState
from .bounded_stream import BoundedStream
from .os import FileOutputStream, file_stat, open_file


class FileSink(DataSink):
    """Implementation of a sink that writes data to filesystem."""

    def __init__(self, fpath: Path):
        """Initialize the sink.

        :param fpath: The path to the file where the data will be written.
        """
        self._fpath = fpath
        self._state = SinkState.NOT_ALLOCATED
        self._file: FileOutputStream | None = None

    def allocate(self, size: int) -> None:
        """Allocate space for the sink."""
        self._file = open_file(self._fpath, mode="wb")
        self._file.truncate(size)
        self._state = SinkState.ALLOCATED

    def open_chunk(self, offset: int = 0) -> OutputStream:  # type: ignore
        """Open a chunk of the sink for writing."""
        if self._state != SinkState.ALLOCATED:
            raise RuntimeError("Sink not allocated")

        chunk = open_file(self._fpath, mode="r+b")
        chunk.seek(offset)
        return chunk

    def close(self) -> None:
        """Close the sink."""
        if self._file is not None:
            with contextlib.suppress(Exception):
                self._file.close()
        self._file = None

        self._state = SinkState.CLOSED

    @property
    def state(self) -> SinkState:
        """Return the current state of the sink."""
        return self._state

    def __repr__(self):
        """Return a string representation of the sink."""
        return f"<{self.__class__.__name__} {self._fpath} {self._state}>"


class FileSource(DataSource):
    """A data source that reads data from a file."""

    has_range_support = True

    def __init__(self, file_name: Path | str):
        """Initialize the data source.

        :param file_name: The name of the file to read from, must exist on the filesystem
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        self._file_name = file_name

    def open(self, offset: int = 0, count: int | None = None) -> InputStream:  # type: ignore
        """Open the file for reading."""
        ret = open_file(self._file_name, mode="rb")
        ret.seek(offset)
        if not count:
            return ret
        else:
            return BoundedStream(ret, count)

    def size(self) -> int:
        """Return the size of the file."""
        return (file_stat(self._file_name)).st_size

    def content_type(self) -> str:
        """Return the content type of the file."""
        f = open_file(self._file_name, mode="rb")
        try:
            data = f.read(2048)
            return magic.from_buffer(data, mime=True)
        finally:
            f.close()

    def close(self) -> None:
        """Close the data source."""
        pass

