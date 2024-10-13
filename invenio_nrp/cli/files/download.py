#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline client for downloading files."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.records.record_file_name import create_output_file_name
from invenio_nrp.client.async_client.files.downloader import Downloader
from invenio_nrp.client.async_client.files.sink.file import FileSink


@run_async
async def download_files(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    keys: Annotated[list[str], typer.Argument(help="File key")],
    output: Annotated[Optional[Path], typer.Option("-o", help="Output path")],
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
) -> None:
    """Download files from a record."""
    output = output or Path.cwd()

    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    if record_id.startswith("@"):
        ids.extend(variables[record_id[1:]])
    else:
        ids.append(record_id)

    async with Downloader() as downloader:
        for record_id in ids:
            record, record_id, repository_config = await read_record(
                record_id, repository, config, False, model, published
            )
            files = await record.files().list()

            # TODO: better way of handling tls verification
            if not repository_config.verify_tls:
                downloader.verify_tls = False

            if "*" in keys:
                keys = [file.key for file in files.entries]
            else:
                keys = list(set(keys) & {file.key for file in files.entries})

            for key in keys:
                try:
                    file = files[key]
                except KeyError:
                    print(f"Key {key} not found in files, skipping ...")
                    continue

                is_file = "{key}" in str(output)

                # sanitize the key
                if "/" in key:
                    key = key.replace("/", "_")
                if ":" in key:
                    key = key.replace(":", "_")

                file_output = create_output_file_name(
                    output,
                    key,
                    file,
                    OutputFormat.JSON,
                    record=record.model_dump(mode="json"),  # type: ignore
                )

                if not is_file:
                    file_output = file_output / key

                if file_output and file_output.parent:
                    file_output.parent.mkdir(parents=True, exist_ok=True)

                downloader.add(str(file.links.content), FileSink(file_output))
