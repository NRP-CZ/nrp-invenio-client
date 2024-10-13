import logging
import traceback
from functools import partial

import humanize
import progressbar

from .progress import ProgressKeeper
from .job import DownloadJob
from .chunk import DownloadChunk
from .downloader import Downloader

log = logging.getLogger(__name__)


def downloaded_size(pb, x):
    value = x["value"]
    if not isinstance(value, int):
        value = 0
    max_value = x["max_value"]
    if not isinstance(max_value, int):
        max_value = 0
    return f"{humanize.naturalsize(value)} / {humanize.naturalsize(max_value)}"


def downloader_stats(pb, x, downloader=None):
    running_connections = downloader.limiter.capacity - downloader.limiter.free
    if running_connections:
        return f"{running_connections} connections running"
    return ""


class ProgressBar(ProgressKeeper):
    def __init__(self):
        self._total_bytes = 0
        self._total_chunks = 0
        self._total_files = 0
        self._pb = None

    def download_file_started(self, job: DownloadJob):
        self._total_files += 1
        print(f"Starting download for {job.url} -> {job.sink}")

    def download_file_info_finished(self, job: DownloadJob):
        self._total_bytes += job.total_size

        print(
            f"Download info finished for {job.url}, file size is {humanize.naturalsize(job.total_size)}"
        )
        self._pb.max_value = job.downloader.total_size
        self._pb.update(job.downloader.downloaded_size)

    def download_chunk_started(self, chunk: DownloadChunk):
        self._total_chunks += 1
        try:
            self._pb.max_value = chunk.downloader.total_size
            self._pb.update(chunk.downloader.downloaded_size)
        except:
            traceback.print_exc()

    def download_file_finished(self, job: DownloadJob):
        self._total_files -= 1
        print(f"Download finished for {job.url} -> {job.sink}")

    def download_chunk_finished(self, chunk: DownloadChunk):
        self._total_chunks -= 1

    def download_file_before_finish(self, job: DownloadJob):
        self._total_bytes -= job.total_size

    def on_error(self, message: str,
                 downloader: "Downloader|None" = None,
                 job: DownloadJob | None = None,
                 chunk: DownloadChunk | None = None):
        log.error(message)

    def downloader_started(self, downloader: "Downloader"):

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
            widgets=widgets, max_value=progressbar.UnknownLength)


    def downloader_before_finish(self, downloader: "Downloader"):
        pass

    def downloader_finished(self, downloader: "Downloader"):
        self._pb.finish()


    def __str__(self):
        return f"Downloaded {self._total_bytes} bytes, {self._total_chunks} chunks, {self._total_files} files"
