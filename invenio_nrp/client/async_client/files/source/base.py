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

    async def open(self, offset: int = 0) -> DataReader:
        """Open the data source for reading.

        :param offset:      where to start reading from
        :return:            a reader for the data source
        """
        ...

    async def size(self) -> int:
        """Returns the length of the data source in bytes."""
        ...

    async def content_type(self) -> str:
        """Returns the content type of the data source."""
        ...

    async def close(self) -> None:
        """Closes the data source."""
        ...
