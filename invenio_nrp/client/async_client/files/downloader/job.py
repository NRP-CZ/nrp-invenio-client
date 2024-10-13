import dataclasses
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .downloader import Downloader

from .chunk import DownloadChunk
from invenio_nrp.client.async_client.files.sink.base import DataSink


@dataclasses.dataclass
class DownloadJob:
    """A single download job (that is, a URL)"""

    downloader: "Downloader"
    """The downloader that is downloading this job"""

    url: str
    """The URL to download"""

    sink: DataSink
    """The sink to save the downloaded data to"""

    auth: Optional[Any] = None
    """The authentication to use for this download"""

    total_chunks: int = 0
    """The total number of chunks that will be downloaded"""

    downloaded_chunks: int = 0
    """The number of chunks that have been downloaded"""

    total_size: Optional[int] = None
    """
    The total size of the file to download. 
    None at the beginning of the download, will be set up when the download starts
    """
    downloaded_size: int = 0

    async def start_downloading(self):
        """Start downloading the file"""
        self.downloader.progress.download_file_started(self)

        async with self.downloader._client() as client:
            # get the location and size of the file
            size, url = await self._get_download_url_and_size(client, self.url)

        # allocate space in the sink
        await self.sink.allocate(size)
        self.total_size = size

        # if the target is empty, just fire the finish download job
        if size == 0:
            self.downloader.create_task(self._finish_download())
            return

        chunk_size = self._get_chunk_size(size)
        chunk_sizes = [
            (offset, min(chunk_size, size - offset))
            for offset in range(0, size, chunk_size)
        ]
        for offset, size in chunk_sizes:
            chunk = DownloadChunk(
                downloader=self.downloader, job=self, offset=offset, size=size
            )
            self.total_chunks += 1
            self.downloader.create_task(chunk.download_chunk())

        self.downloader.progress.download_file_info_finished(self)


    async def _get_download_url_and_size(self, client, url):
        for r in range(self.downloader.max_redirects):
            async with client.options(url, allow_redirects=False) as response:
                if response.status == 302:
                    url = response.headers.get("Location", url)
                    continue
                size = int(response.headers.get("Content-Length", 0))
                break
        else:
            raise Exception("Too many redirects")
        if size == 0:
            # try to read 1 byte
            async with client.get(url, headers={"Range": "bytes=0-0"}) as response:
                content_range = response.headers.get("Content-Range")
                if content_range:
                    content_range = content_range.split("/")
                    if len(content_range) > 1:
                        size = int(content_range[1])

        return size, url

    def chunk_finished(self, size: int):
        """Called when a chunk has been successfully downloaded"""
        self.downloaded_chunks += 1
        self.downloaded_size += size

        if self.downloaded_chunks == self.total_chunks:
            self.downloader.create_task(self._finish_download())

    async def _finish_download(self):
        self.downloader.progress.download_file_before_finish(self)
        try:
            await self.sink.close()
            self.downloader.progress.download_file_finished(self)
        except Exception as e:
            print(f"Error closing sink: {e}")

    def _get_chunk_size(self, size):
        # if the file is very small, just download the whole file
        if size < self.downloader.min_chunk_size:
            return size

        if size < self.downloader.max_chunk_size:
            # check if there is still a space and if so, divide the file into chunks
            empty_slots = self.downloader.limiter.free
            if empty_slots > 0:
                chunk_size = size // empty_slots
                return max(chunk_size, self.downloader.min_chunk_size)

            # if not, just download as a single chunk
            return size

        # split into chunks of max_chunk_size
        return self.downloader.max_chunk_size
