from ..os import DataReader


class BoundedStream:
    def __init__(self, stream: DataReader, limit: int):
        self._stream = stream
        self._remaining = limit

    async def read(self, size=None):
        if self._remaining <= 0:
            return b""
        if size is None:
            size = self._remaining
        data = await self._stream.read(min(size, self._remaining))
        self._remaining -= len(data)
        return data

    async def close(self):
        await self._stream.close()

    def __getattr__(self, name):
        return getattr(self._stream, name)