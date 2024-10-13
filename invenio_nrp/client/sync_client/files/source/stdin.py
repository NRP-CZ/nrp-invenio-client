#
# This file was generated from the asynchronous client at files/source/stdin.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


import contextlib
from pathlib import Path
from typing import Iterator

from .base import DataSource

from ..os import DataReader, file_stat, open_file


class StdInDataSource(DataSource):
    """A data source that reads data from standard input."""

    has_range_support = False

    # TODO: how to correctly type this?
    @contextlib.contextmanager
    def open(self, offset: int = 0) -> Iterator[DataReader]: # type: ignore
        ret = open_file(Path('/sys/stdin'), mode="rb")
        yield ret
        ret.close()

    def size(self) -> int:
        return -1

    def content_type(self) -> str:
        return "application/octet-stream"

    def close(self) -> None:
        """Closes the data source."""
        pass
