#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline client for the downloader."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from .....config import Config
from ...connection.auth import BearerAuthentication, BearerTokenForHost
from ..sink.file import FileSink
from .downloader import Downloader
from .progress_bar import ProgressBar


async def _main(downloader_jobs: list[tuple[str, Path]]) -> None:
    """Download files from the NRP Invenio API to a local file system."""
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
) -> None:
    """Download files from the given urls and save them to the local files.

    Authentication will be taken either
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
