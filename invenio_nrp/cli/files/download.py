#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from functools import partial
from pathlib import Path
from typing import List, Optional

import requests
import typer
from rich.console import Console
from typing_extensions import Annotated
from yarl import URL

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.get import read_record, create_output_file_name, get_repository_from_record_id
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.files import File, FilesList
from invenio_nrp.client.async_client.files.downloader import Downloader
from invenio_nrp.client.async_client.files.sink.file import FileSink
from invenio_nrp.client.async_client.records import RecordClient
from invenio_nrp.client.doi import resolve_doi
from rich import box
from rich.table import Table



@run_async
async def download_files(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    keys: Annotated[List[str], typer.Argument(help="File key")],
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Output path")
    ] = Path.cwd(),
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
):
    console = Console()
    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    if record_id.startswith("@"):
        ids.extend(variables[record_id[1:]])
    else:
        ids.append(record_id)

    async with Downloader() as downloader:
        for record_id in ids:
            record, record_id, repository_config = await read_record(record_id, repository, config, False, model, published)
            files = await record.files().list()

            # TODO: better way of handling tls verification
            if not repository_config.verify_tls:
                downloader.verify_tls = False

            if '*' in keys:
                keys = [file.key for file in files.entries]
            else:
                keys = set(keys) & {file.key for file in files.entries}

            for key in keys:
                try:
                    file = files[key]
                except KeyError:
                    print(f"Key {key} not found in files, skipping ...")
                    continue

                if '{key}' in str(output):
                    is_file = True
                else:
                    is_file = False
                # sanitize the key
                if '/' in key:
                    key = key.replace('/', '_')
                if ':' in key:
                    key = key.replace(':', '_')

                file_output = create_output_file_name(
                    output, key, file, None,
                    record=record.model_dump(mode='json')
                )
                if not is_file:
                    file_output = file_output / key

                if file_output and file_output.parent:
                    file_output.parent.mkdir(parents=True, exist_ok=True)

                downloader.add(file.links.content, FileSink(file_output))


def format_files_table(record, files: FilesList[File]):
    table = Table(
        "Key", "Status", "Mimetype", "Access", "Metadata", "Content URL",
        title=f"Files for record {record.id}",
        box=box.SIMPLE, title_justify="left")
    for file in files.entries:
        table.add_row(file.key, file.status, file.mimetype,
                      str(file.access), str(file.metadata),
                      str(file.links.content))
    yield table