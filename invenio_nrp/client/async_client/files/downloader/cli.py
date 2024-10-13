import asyncio
from pathlib import Path
from typing import Annotated

from invenio_nrp import Config
from ...connection.auth import BearerTokenForHost, BearerAuthentication
from .downloader import Downloader
from .progress_bar import ProgressBar
from ..sink.file import FileSink

import typer

async def _main(downloader_jobs):
    """A commandline client to download files from the NRP Invenio API"""

    config = Config.from_file()
    auth_tokens = []
    for repo in config.repositories:
        if repo.token:
            auth_tokens.append(BearerTokenForHost(repo.url, repo.token))

    async with Downloader(
        progress=ProgressBar(), auth=BearerAuthentication(auth_tokens)
    ) as downloader:
        for url, file in downloader_jobs:
            downloader.add(url=url, sink=FileSink(file))


app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def main(
    urls: Annotated[
        list[str],
        typer.Argument(
            help="A list of urls to download. Might be in the form of 'url' or 'url->local_file_path'"
        ),
    ],
):
    """Download files from the given urls and save them to the local files. Authentication will be taken either
    from the ~/.nrp/invenio-config.json (Bearer tokens if the file is downloaded from a configured repository)
    or from .netrc.
    """
    downloader_jobs = []
    while len(urls):
        url = urls.pop(0)
        if "->" in url:
            url, file = url.split("->")
            file_path = Path(file)
        else:
            file_path = Path(url.split("/")[-1])
        downloader_jobs.append((url, file_path))
    asyncio.run(_main(downloader_jobs))


if __name__ == "__main__":
    app()
