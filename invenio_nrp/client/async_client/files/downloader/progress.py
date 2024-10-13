from typing import TYPE_CHECKING

from invenio_nrp.client.async_client.files.downloader.progress_bar import log

if TYPE_CHECKING:
    from .downloader import Downloader
    from .job import DownloadJob
    from .chunk import DownloadChunk


class ProgressKeeper:
    def on_error(self, message: str,
                 downloader: "Downloader|None" = None, job: DownloadJob | None = None,
                 chunk: DownloadChunk | None = None):
        log.error(message)

    def download_file_started(self, job: DownloadJob):
        pass

    def download_file_info_finished(self, job: DownloadJob):
        pass

    def download_chunk_started(self, chunk: DownloadChunk):
        pass

    def download_chunk_finished(self, chunk: DownloadChunk):
        pass

    def download_file_before_finish(self, job: DownloadJob):
        pass

    def download_file_finished(self, job: DownloadJob):
        pass

    def downloader_started(self, downloader: "Downloader"):
        pass

    def downloader_before_finish(self, downloader: "Downloader"):
        pass

    def downloader_finished(self, downloader: "Downloader"):
        pass

    def warning(self, downloader: "Downloader", job: DownloadJob, message: str):
        log.warning(message)
