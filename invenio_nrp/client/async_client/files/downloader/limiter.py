import asyncio


class Limiter(asyncio.Semaphore):
    """A class to limit the number of simultaneous connections"""

    def __init__(self, capacity):
        """Initialize the limiter

        :param capacity:    the number of simultaneous connections
        """
        self.capacity = capacity
        super().__init__(capacity)

    @property
    def free(self):
        """The number of free slots

        :return:   the number of remaining connections
        """
        return self._value
