#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Progress keeper for the downloader."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chunk import DownloadChunk
    from .downloader import Downloader
    from .job import DownloadJob


class ProgressKeeper:
    """Progress keeper for the downloader."""

    def on_error(
        self,
        message: str,
        downloader: Downloader | None = None,
        job: DownloadJob | None = None,
        chunk: DownloadChunk | None = None,
    ) -> None:
        """Log an error message."""
        pass

    def download_file_started(self, job: DownloadJob) -> None:
        """Note that a file download has started."""
        pass

    def download_file_info_finished(self, job: DownloadJob) -> None:
        """Note that the file info has been downloaded."""
        pass

    def download_chunk_started(self, chunk: DownloadChunk) -> None:
        """Note that a chunk download has started."""
        pass

    def download_chunk_finished(self, chunk: DownloadChunk) -> None:
        """Note that a chunk download has finished."""
        pass

    def download_file_before_finish(self, job: DownloadJob) -> None:
        """Note that the file download is about to finish."""
        pass

    def download_file_finished(self, job: DownloadJob) -> None:
        """Note that the file download has finished."""
        pass

    def downloader_started(self, downloader: Downloader) -> None:
        """Note that the downloader has started."""
        pass

    def downloader_before_finish(self, downloader: Downloader) -> None:
        """Note that the downloader is about to finish."""
        pass

    def downloader_finished(self, downloader: Downloader) -> None:
        """Note that the downloader has finished."""
        pass

    def warning(self, downloader: Downloader, job: DownloadJob, message: str) -> None:
        """Log a warning message."""
        pass
