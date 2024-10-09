#
# This file was generated from the asynchronous client at files/source/base.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Protocol for data sources."""
from typing import Protocol

from ..os import DataReader


class DataSource(Protocol):
    """Protocol for data sources."""

    def open(self, offset: int = 0) -> DataReader:
        """
        Open the data source for reading.

        :param offset:      where to start reading from
        :return:            a reader for the data source
        """
        ...

    def size(self) -> int:
        """Returns the length of the data source in bytes."""
        ...

    def content_type(self) -> str:
        """Returns the content type of the data source."""
        ...

    def close(self) -> None:
        """Closes the data source."""
        ...