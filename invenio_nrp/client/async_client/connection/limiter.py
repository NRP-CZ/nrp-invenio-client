#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Contains the limiter class for limiting the number of simultaneous connections."""

import asyncio


class Limiter(asyncio.Semaphore):
    """A class to limit the number of simultaneous connections."""

    def __init__(self, capacity: int):
        """Initialize the limiter.

        :param capacity:    the number of simultaneous connections
        """
        self.capacity = capacity
        super().__init__(capacity)

    @property
    def free(self) -> int:
        """The number of free slots.

        :return:   the number of remaining connections
        """
        return self._value
