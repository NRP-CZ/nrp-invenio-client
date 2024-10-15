#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Console progress bar for the downloader."""

from __future__ import annotations

import logging
import traceback
from functools import partial
from typing import TYPE_CHECKING

import humanize
import progressbar

from .progress import ProgressKeeper

if TYPE_CHECKING:
    from .chunk import DownloadChunk
    from .downloader import Downloader
    from .job import DownloadJob

log = logging.getLogger(__name__)


def downloaded_size(pb: progressbar.ProgressBar, x: dict) -> str:
    """Format the downloaded size."""
    value = x["value"]
    if not isinstance(value, int):
        value = 0
    max_value = x["max_value"]
    if not isinstance(max_value, int):
        max_value = 0
    return f"{humanize.naturalsize(value)} / {humanize.naturalsize(max_value)}"


def downloader_stats(
    pb: progressbar.ProgressBar, x: dict, *, downloader: Downloader
) -> str:
    """Format the downloader stats."""
    running_connections = downloader.limiter.capacity - downloader.limiter.free
    if running_connections:
        return f"{running_connections} connections running"
    return ""


class ProgressBar(ProgressKeeper):
    """Console progress bar for the downloader."""

    def __init__(self):
        """Initialize the progress bar."""
        self._total_bytes = 0
        self._total_chunks = 0
        self._total_files = 0
        self._pb = None

    def download_file_started(self, job: DownloadJob) -> None:
        """Note that a file download has started."""
        self._total_files += 1
        print(f"Starting download for {job.url} -> {job.sink}")

    def download_file_info_finished(self, job: DownloadJob) -> None:
        """Note that the file info has been downloaded."""
        self._total_bytes += job.total_size

        print(
            f"Download info finished for {job.url}, file size is {humanize.naturalsize(job.total_size)}"
        )
        self._pb.max_value = job.downloader.total_size
        self._pb.update(job.downloader.downloaded_size)

    def download_chunk_started(self, chunk: DownloadChunk) -> None:
        """Note that a chunk download has started."""
        self._total_chunks += 1
        try:
            self._pb.max_value = chunk.downloader.total_size
            self._pb.update(chunk.downloader.downloaded_size)
        except:  # noqa
            traceback.print_exc()

    def download_file_finished(self, job: DownloadJob) -> None:
        """Note that the file download has finished."""
        self._total_files -= 1
        print(f"Download finished for {job.url} -> {job.sink}")

    def download_chunk_finished(self, chunk: DownloadChunk) -> None:
        """Note that a chunk download has finished."""
        self._total_chunks -= 1

    def download_file_before_finish(self, job: DownloadJob) -> None:
        """Note that the file download is about to finish."""
        self._total_bytes -= job.total_size

    def on_error(
        self,
        message: str,
        downloader: Downloader | None = None,
        job: DownloadJob | None = None,
        chunk: DownloadChunk | None = None,
    ) -> None:
        """Log an error message."""
        log.error(message)

    def downloader_started(self, downloader: Downloader) -> None:
        """Note that the downloader has started."""
        widgets = [
            "Downloaded ",
            downloaded_size,
            " ",
            progressbar.GranularBar(),
            " ",
            progressbar.Percentage(),
            " ",
            progressbar.FileTransferSpeed(),
            " ",
            progressbar.ETA(),
            ", ",
            partial(downloader_stats, downloader=downloader),
        ]

        self._pb = progressbar.ProgressBar(
            widgets=widgets, max_value=progressbar.UnknownLength
        )

    def downloader_before_finish(self, downloader: Downloader) -> None:
        """Note that the downloader is about to finish."""
        pass

    def downloader_finished(self, downloader: Downloader) -> None:
        """Note that the downloader has finished."""
        self._pb.finish()

    def __str__(self) -> str:
        """Return the progress bar stats."""
        return f"Downloaded {self._total_bytes} bytes, {self._total_chunks} chunks, {self._total_files} files"
