#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, run_async
from invenio_nrp.cli.records.get import read_record, get_single_record
from invenio_nrp.client.async_client.files.downloader import Downloader
from invenio_nrp.client.async_client.files.sink.file import FileSink


@run_async
async def download_record(
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Save the output to a file")
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("-f", help="The format of the output"),
    ] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    expand: Annotated[bool, typer.Option(help="Expand the record")] = False,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
    record_ids: Annotated[List[str], typer.Argument(help="Record ID")] = None,
):
    console = Console()
    config = Config.from_file()

    ids = []
    for rec_id in record_ids:
        if rec_id.startswith("@"):
            ids.extend(config.get_variable(rec_id))
        else:
            ids.append(rec_id)

    async with Downloader() as downloader:
        for record_id in ids:
            await download_single_record(
                downloader,
                record_id,
                console,
                config,
                repository,
                model,
                output,
                output_format,
                published,
                draft,
                expand,
            )


async def download_single_record(
    downloader: Downloader,
    record_id,
    console,
    config,
    repository,
    model,
    output,
    output_format,
    published,
    draft,
    expand,
):
    # 1. download record metadata
    if not output:
        output = Path("{id}")

    if not output_format:
        output_format = OutputFormat.JSON

    record, output, repository_config = await get_single_record(
        record_id,
        console,
        config,
        repository,
        model,
        output / "metadata{ext}",
        output_format,
        published,
        draft,
        expand,
    )

    output_dir = output.parent

    # TODO: better way of handling tls verification
    if not repository_config.verify_tls:
        downloader.verify_tls = False

    # 2. download record files
    files = await record.files().list()
    for file in files.entries:
        file_path = output_dir / file.key
        downloader.add(str(file.links.content), FileSink(file_path))
