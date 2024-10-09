#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""
A downloader for potentially large files that can be used to download files from the NRP Invenio API
and save them to a local file.

Usage:

async def on_progress(downloader, event, job, message=None):
    if event == ProgressEvent.CHUNK_FINISHED:
        print(f"Downloaded {downloader.total_bytes} bytes, {downloader.total_chunks} chunks, {downloader.total_files} files")

with Downloader(on_progress=on_progress, auth=SomeAuth()) as downloader:
    downloader.add(url="https://example.com/file", sink=FileSink(Path("output.txt")))
"""

import asyncio
import contextlib
import dataclasses
import traceback
from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated, Any, Callable, List, Optional

import typer.cli
from aiohttp import ClientSession, TCPConnector
from aiohttp_retry import RetryClient

from invenio_nrp.client.async_client.connection.auth import (
    AuthenticatedClientRequest,
    Authentication,
    BearerAuthentication,
)
from invenio_nrp.client.async_client.connection.retry import ServerAssistedRetry
from invenio_nrp.client.async_client.files.sink.file import FileSink
from invenio_nrp.config import Config
from invenio_nrp.types.base import URLBearerToken

from .sink.base import DataSink


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
        """
        Start downloading the file
        """
        self._send_progress(ProgressEvent.DOWNLOAD_FILE_STARTED)

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

        self._send_progress(ProgressEvent.DOWNLOAD_FILE_INFO_FINISHED)

    def _send_progress(self, event, message=None):
        self.downloader._send_progress(event, job=self, message=message)

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

        self._send_progress(ProgressEvent.DOWNLOAD_CHUNK_FINISHED)

        if self.downloaded_chunks == self.total_chunks:
            self.downloader.create_task(self._finish_download())

    async def _finish_download(self):
        self._send_progress(ProgressEvent.DOWNLOAD_FILE_BEFORE_FINISH)
        try:
            await self.sink.close()
        except Exception as e:
            print(f"Error closing sink: {e}")
        finally:
            self._send_progress(ProgressEvent.DOWNLOAD_FILE_FINISHED)

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


@dataclasses.dataclass
class DownloadChunk:
    """A single chunk of a download job"""

    downloader: "Downloader"
    """The downloader that is downloading this chunk"""

    job: DownloadJob
    """The job that this chunk belongs to"""

    offset: int = 0
    """The offset of the chunk in the downloaded file"""

    size: int = 0
    """The size of the chunk"""

    async def download_chunk(self):
        """Method that downloads the chunk and retries the download if needed."""
        initial_size = self.size
        async with self.downloader.limiter:
            self._send_progress(ProgressEvent.DOWNLOAD_CHUNK_STARTED)

            async with self.downloader._client() as client:
                for try_ in range(self.downloader.retry_count):
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
                        self._send_progress(
                            ProgressEvent.WARNING,
                            message=f"Error downloading chunk {self.offset}-{self.offset + self.size - 1}: {e}",
                        )
                else:
                    self._send_progress(
                        ProgressEvent.ERROR,
                        message=f"Failed to download chunk {self._get_range_header()}",
                    )
                    raise Exception(
                        f"Failed to download chunk {self._get_range_header()} for job {self.job}"
                    )

        self.job.chunk_finished(initial_size)

    def _send_progress(self, event, message=None):
        self.downloader._send_progress(event, job=self.job, message=message)

    async def _get_range_header(self):
        if self.size:
            range_header = f"bytes={self.offset}-{self.offset + self.size - 1}"
        else:
            range_header = f"bytes={self.offset}-"
        return range_header

    async def _save_stream_to_sink(self, response):
        async with self.job.sink.open_chunk(self.offset) as sink_stream:
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


class ProgressEvent(StrEnum):
    ERROR = auto()
    DOWNLOAD_FILE_STARTED = auto()
    DOWNLOAD_FILE_INFO_FINISHED = auto()

    DOWNLOAD_CHUNK_STARTED = auto()
    DOWNLOAD_CHUNK_FINISHED = auto()

    DOWNLOAD_FILE_BEFORE_FINISH = auto()
    DOWNLOAD_FILE_FINISHED = auto()

    DOWNLOADER_BEFORE_FINISH = auto()
    DOWNLOADER_FINISHED = auto()

    WARNING = auto()


class Limiter(asyncio.Semaphore):
    """A class to limit the number of simultaneous connections"""

    def __init__(self, capacity):
        """
        Initialize the limiter

        :param capacity:    the number of simultaneous connections
        """
        self.capacity = capacity
        super().__init__(capacity)

    @property
    def free(self):
        """
        The number of free slots

        :return:   the number of remaining connections
        """
        return self._value


global_limiter = Limiter(10)


@dataclasses.dataclass
class Downloader:
    """
    A downloader for potentially large files that can be used to download files from the NRP Invenio API
    or other https sources
    """

    min_chunk_size: int = 65536 * 2  # 128KB
    """Will use this chunk size if the file is smaller than max_chunk_size"""

    max_chunk_size: int = 10 * 1024 * 1024  # 10MB
    """The maximum chunk size, will be used when the file is larger"""

    block_size: int = 65536  # 64KB
    """Memory block size for downloading the file. The total memory will be around block_size * limiter.capacity"""

    verify_tls: bool = True
    """Whether to verify the TLS certificate"""

    retry_count: int = 5
    """The number of retries to do if the download fails"""

    retry_after_seconds: int = 5
    """The number of seconds to wait before the next retry if the server does not send an interval in 429 header"""

    max_redirects: int = 5
    """The maximum number of redirects to follow"""

    auth: Optional[Authentication] = None
    """The authentication to use for the download"""

    on_progress: Callable[
        ["Downloader", ProgressEvent, Optional[DownloadJob], Optional[str]], None
    ] = lambda slf, event, job, msg: None
    """The callback to call when a progress event happens"""

    limiter: Limiter = global_limiter
    """The limiter to use for the download, defaults to a global one with 10 simultaneous connections"""

    _tg: Optional[asyncio.TaskGroup] = None
    """Asyncio task group for the downloader"""

    _internal_lock: asyncio.Lock = asyncio.Lock()
    """Internal lock to protect the state of the downloader"""

    _download_jobs: List[DownloadJob] = dataclasses.field(default_factory=list)
    """List of download jobs"""

    async def __aenter__(self):
        # start the job group
        self._tg = asyncio.TaskGroup()
        await self._tg.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # finish all pending downloads
        self._send_progress(ProgressEvent.DOWNLOADER_BEFORE_FINISH, None)
        try:
            return await self._tg.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._send_progress(ProgressEvent.DOWNLOADER_FINISHED, None)

    def add(self, url: str, sink: DataSink, auth: Optional[Any] = None):
        """
        Add a new download job, will be started when capacity allows

        :param url:         url of the file to be downloaded
        :param sink:        sink to save the downloaded data to
        :param auth:        authentication to use for this download
        """
        self._tg.create_task(self._start_download(url=url, sink=sink, auth=auth))

    async def _start_download(
        self, url: str, sink: DataSink, auth: Optional[Any] = None
    ):
        """
        Internal method to start the download, guarded by the limiter

        :param url:         url of the file to be downloaded
        :param sink:        sink to save the downloaded data to
        :param auth:        authentication to use for this download
        """
        async with self.limiter:
            job = DownloadJob(downloader=self, url=url, sink=sink, auth=auth)
            self._download_jobs.append(job)
            self._tg.create_task(job.start_downloading())

    def _send_progress(
        self, event: ProgressEvent, job: Optional[DownloadJob], message=None
    ):
        self.on_progress(self, event, job, message)

    def create_task(self, task: Any):
        """
        Creates a new task, called from job & chunk

        :param task:        coro to be executed
        """
        return self._tg.create_task(task)

    async def stop(self):
        """
        Abort all downloads
        """
        if self._tg:
            await self._tg._abort()  # noqa

    @contextlib.asynccontextmanager
    async def _client(self) -> RetryClient:
        """
        Create a new session with the repository and configure it with the token.
        :return: A new http client
        """
        connector = TCPConnector(verify_ssl=self.verify_tls)

        async with ClientSession(
            request_class=AuthenticatedClientRequest,
            connector=connector,
            auth=self.auth,
        ) as session:
            retry_client = RetryClient(
                client_session=session,
                retry_options=ServerAssistedRetry(
                    attempts=self.retry_count,
                    start_timeout=self.retry_after_seconds,
                ),
            )
            yield retry_client

    @property
    def has_capacity(self):
        """
        Check if there is a free slot in the limiter

        :return:    True if can start an immediate download
        """
        return self.limiter.free > 0

    @property
    def total_chunks(self):
        """
        The total number of chunks that will be downloaded

        :return:    the total number of chunks
        """
        return sum(job.total_chunks for job in self._download_jobs)

    @property
    def downloaded_chunks(self):
        """
        The number of chunks that have been downloaded

        :return:    the number of downloaded chunks
        """
        return sum(job.downloaded_chunks for job in self._download_jobs)

    @property
    def total_jobs(self):
        """
        The total number of download jobs

        :return:    the total number of jobs
        """
        return len(self._download_jobs)

    @property
    def downloaded_jobs(self):
        """
        The number of jobs that have been downloaded

        :return:    the number of downloaded jobs
        """
        return sum(
            1
            for job in self._download_jobs
            if job.downloaded_chunks == job.total_chunks
        )

    @property
    def total_size(self):
        """
        The total size of the files to download

        :return:    the total size of the files
        """
        return sum((job.total_size or 0) for job in self._download_jobs)

    @property
    def downloaded_size(self):
        """
        The total size of the downloaded files

        :return:  the total size of the downloaded files
        """
        return sum(job.downloaded_size for job in self._download_jobs)


async def _main(downloader_jobs):
    """A commandline client to download files from the NRP Invenio API"""
    import humanize
    import progressbar

    downloader = None

    def downloaded_size(pb, x):
        value = x["value"]
        if not isinstance(value, int):
            value = 0
        max_value = x["max_value"]
        if not isinstance(max_value, int):
            max_value = 0
        return f"{humanize.naturalsize(value)} / {humanize.naturalsize(max_value)}"

    def downloader_stats(pb, x):
        running_connections = downloader.limiter.capacity - downloader.limiter.free
        if running_connections:
            return f"{running_connections} connections running"
        return ""

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
        downloader_stats,
    ]
    with progressbar.ProgressBar(
        widgets=widgets, max_value=progressbar.UnknownLength
    ) as bar:

        def on_progress(
            downloader: Downloader, event: ProgressEvent, job: DownloadJob, message: str
        ):
            match event:
                case ProgressEvent.DOWNLOAD_CHUNK_FINISHED:
                    try:
                        bar.max_value = downloader.total_size
                        bar.update(downloader.downloaded_size)
                    except:
                        traceback.print_exc()
                case ProgressEvent.DOWNLOAD_FILE_STARTED:
                    print(f"Starting download for {job.url} -> {job.sink}")
                case ProgressEvent.DOWNLOAD_FILE_INFO_FINISHED:
                    print(
                        f"Download info finished for {job.url}, file size is {humanize.naturalsize(job.total_size)}"
                    )
                    bar.max_value = downloader.total_size
                    bar.update(downloader.downloaded_size)
                case ProgressEvent.DOWNLOAD_FILE_FINISHED:
                    print(f"Download finished for {job.url} -> {job.sink}")
                case ProgressEvent.DOWNLOADER_FINISHED:
                    bar.finish()
                case _:
                    pass

        config = Config.from_file()
        auth_tokens = []
        for repo in config.repositories:
            if repo.token:
                auth_tokens.append(URLBearerToken(repo.url, repo.token))

        async with asyncio.TaskGroup() as tg:
            pass

        async with Downloader(
            on_progress=on_progress, auth=BearerAuthentication(auth_tokens)
        ) as downloader:
            for url, file in downloader_jobs:
                downloader.add(url=url, sink=FileSink(file))


app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def main(
    urls: Annotated[
        List[str],
        typer.Argument(
            help="A list of urls to download. Might be in the form of 'url' or 'url->local_file_path'"
        ),
    ]
):
    """
    Download files from the given urls and save them to the local files. Authentication will be taken either
    from the ~/.nrp/invenio-config.json (Bearer tokens if the file is downloaded from a configured repository)
    or from .netrc.
    """
    downloader_jobs = []
    while len(urls):
        url = urls.pop(0)
        if "->" in url:
            url, file = url.split("->")
            file = Path(file)
        else:
            file = Path(url.split("/")[-1])
        downloader_jobs.append((url, file))
    asyncio.run(_main(downloader_jobs))


if __name__ == "__main__":
    app()
