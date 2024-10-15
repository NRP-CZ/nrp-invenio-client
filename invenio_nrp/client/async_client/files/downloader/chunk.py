#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Downloader chunk."""

from __future__ import annotations

import dataclasses
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import ClientResponse

    from .downloader import Downloader, DownloadJob


@dataclasses.dataclass
class DownloadChunk:
    """A single chunk of a download job."""

    downloader: Downloader
    """The downloader that is downloading this chunk"""

    job: DownloadJob
    """The job that this chunk belongs to"""

    offset: int = 0
    """The offset of the chunk in the downloaded file"""

    size: int = 0
    """The size of the chunk"""

    async def download_chunk(self) -> None:
        """Download the chunk and retry the download if needed."""
        initial_size = self.size
        async with self.downloader.limiter:
            self.downloader.progress.download_chunk_started(self)
            async with self.downloader._client() as client:
                for _ in range(self.downloader.retry_count):
                    try:
                        range_header = await self._get_range_header()

                        async with client.get(
                            self.job.url, headers={"Range": range_header}
                        ) as response:
                            response.raise_for_status()
                            await self._save_stream_to_sink(response)
                        break
                    except Exception as e:
                        traceback.print_exc()
                        self.downloader.progress.on_error(
                            f"Error downloading chunk {self.offset}-{self.offset + self.size - 1}: {e}",
                        )
                else:
                    self.downloader.progress.on_error(
                        f"Failed to download chunk {self._get_range_header()}",
                    )
                    raise Exception(
                        f"Failed to download chunk {self._get_range_header()} for job {self.job}"
                    )
            self.downloader.progress.download_chunk_finished(self)
        self.job.chunk_finished(initial_size)

    async def _get_range_header(self) -> str:
        if self.size:
            range_header = f"bytes={self.offset}-{self.offset + self.size - 1}"
        else:
            range_header = f"bytes={self.offset}-"
        return range_header

    async def _save_stream_to_sink(self, response: ClientResponse) -> None:
        async with self.job.sink.open_chunk(self.offset) as sink_stream:  # type: ignore
            chunk: bytes
            async for chunk in response.content.iter_chunked(
                self.downloader.block_size
            ):
                if len(chunk) > self.size:
                    chunk = chunk[: self.size]
                await sink_stream.write(chunk)
                self.offset += len(chunk)
                self.size -= len(chunk)
                if not self.size:
                    break
