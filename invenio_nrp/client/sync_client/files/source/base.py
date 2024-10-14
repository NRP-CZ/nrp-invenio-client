#
# This file was generated from the asynchronous client at files/source/base.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Protocol for data sources."""

from typing import ContextManager, Protocol

from ..os import DataReader


class DataSource(Protocol):
    """Protocol for data sources."""

    has_range_support: bool = False

    def open(self, offset: int = 0) -> ContextManager[DataReader]:
        """Open the data source for reading.

        :param offset:      where to start reading from
        :return:            a reader for the data source
        """
        ...

    def size(self) -> int:
        """Return the length of the data source in bytes."""
        ...

    def content_type(self) -> str:
        """Return the content type of the data source."""
        ...

    def close(self) -> None:
        """Close the data source."""
        ...
