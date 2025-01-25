#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Protocol for data sources."""

from typing import AsyncContextManager, Protocol

from ..os import DataReader


class DataSource(Protocol):
    """Protocol for data sources."""

    has_range_support: bool = False

    async def open(self, offset: int = 0, count: int | None = None) -> AsyncContextManager[DataReader]:
        """Open the data source for reading.

        :param offset:      where to start reading from
        :param count:       how many bytes to read, if None, read until the end
        :return:            a reader for the data source
        """
        ...

    async def size(self) -> int:
        """Return the length of the data source in bytes."""
        ...

    async def content_type(self) -> str:
        """Return the content type of the data source."""
        ...

    async def close(self) -> None:
        """Close the data source."""
        ...
