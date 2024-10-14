#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#

#
# This file was generated from the asynchronous client at files/source/file.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""File data source."""

import contextlib
from pathlib import Path
from typing import Iterator

import magic

from ..os import DataReader, file_stat, open_file
from .base import DataSource


class FileDataSource(DataSource):
    """A data source that reads data from a file."""

    has_range_support = True

    def __init__(self, file_name: Path | str):
        """Initialize the data source.

        :param file_name: The name of the file to read from, must exist on the filesystem
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        self._file_name = file_name

    # TODO: how to correctly type this?
    @contextlib.contextmanager
    def open(self, offset: int = 0) -> Iterator[DataReader]:  # type: ignore
        """Open the file for reading."""
        ret = open_file(self._file_name, mode="rb")
        ret.seek(offset)
        yield ret
        ret.close()

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
