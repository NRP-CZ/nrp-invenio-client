import asyncio
import contextlib
import dataclasses
from typing import Optional, Any

from aiohttp import TCPConnector, ClientSession
from aiohttp_retry import RetryClient

from invenio_nrp.client.async_client.connection.auth import Authentication, AuthenticatedClientRequest
from invenio_nrp.client.async_client.connection.retry import ServerAssistedRetry
from .limiter import Limiter
from .progress import ProgressKeeper
from .job import DownloadJob
from invenio_nrp.client.async_client.files.sink.base import DataSink

global_limiter = Limiter(10)


@dataclasses.dataclass
class Downloader:
    """A downloader for potentially large files that can be used to download files from the NRP Invenio API
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

    progress: ProgressKeeper = dataclasses.field(default_factory=ProgressKeeper)
    """The callback to call when a progress event happens"""

    limiter: Limiter = global_limiter
    """The limiter to use for the download, defaults to a global one with 10 simultaneous connections"""

    _tg: Optional[asyncio.TaskGroup] = None
    """Asyncio task group for the downloader"""

    _internal_lock: asyncio.Lock = asyncio.Lock()
    """Internal lock to protect the state of the downloader"""

    _download_jobs: list[DownloadJob] = dataclasses.field(default_factory=list)
    """List of download jobs"""

    async def __aenter__(self):
        # start the job group
        self._tg = asyncio.TaskGroup()
        await self._tg.__aenter__()
        self.progress.downloader_started(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # finish all pending downloads
        self.progress.downloader_before_finish(self)
        try:
            return await self._tg.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self.progress.downloader_finished(self)

    def add(self, url: str, sink: DataSink, auth: Optional[Any] = None):
        """Add a new download job, will be started when capacity allows

        :param url:         url of the file to be downloaded
        :param sink:        sink to save the downloaded data to
        :param auth:        authentication to use for this download
        """
        assert self._tg, "Downloader not started"
        self._tg.create_task(self._start_download(url=url, sink=sink, auth=auth))

    async def _start_download(
        self, url: str, sink: DataSink, auth: Optional[Any] = None
    ):
        """Internal method to start the download, guarded by the limiter

        :param url:         url of the file to be downloaded
        :param sink:        sink to save the downloaded data to
        :param auth:        authentication to use for this download
        """
        async with self.limiter:
            job = DownloadJob(downloader=self, url=url, sink=sink, auth=auth)
            self._download_jobs.append(job)
            assert self._tg, "Downloader not started"
            self._tg.create_task(job.start_downloading())


    def create_task(self, task: Any):
        """Creates a new task, called from job & chunk

        :param task:        coro to be executed
        """
        assert self._tg, "Downloader not started"
        return self._tg.create_task(task)

    async def stop(self):
        """Abort all downloads"""
        if self._tg:
            await self._tg._abort()  # noqa

    @contextlib.asynccontextmanager
    async def _client(self) -> RetryClient:
        """Create a new session with the repository and configure it with the token.
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
        """Check if there is a free slot in the limiter

        :return:    True if can start an immediate download
        """
        return self.limiter.free > 0

    @property
    def total_chunks(self):
        """The total number of chunks that will be downloaded

        :return:    the total number of chunks
        """
        return sum(job.total_chunks for job in self._download_jobs)

    @property
    def downloaded_chunks(self):
        """The number of chunks that have been downloaded

        :return:    the number of downloaded chunks
        """
        return sum(job.downloaded_chunks for job in self._download_jobs)

    @property
    def total_jobs(self):
        """The total number of download jobs

        :return:    the total number of jobs
        """
        return len(self._download_jobs)

    @property
    def downloaded_jobs(self):
        """The number of jobs that have been downloaded

        :return:    the number of downloaded jobs
        """
        return sum(
            1
            for job in self._download_jobs
            if job.downloaded_chunks == job.total_chunks
        )

    @property
    def total_size(self):
        """The total size of the files to download

        :return:    the total size of the files
        """
        return sum((job.total_size or 0) for job in self._download_jobs)

    @property
    def downloaded_size(self) -> int:
        """The total size of the downloaded files

        :return:  the total size of the downloaded files
        """
        return sum(job.downloaded_size for job in self._download_jobs)
