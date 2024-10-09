#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, set_variable
from invenio_nrp.cli.files.upload import upload_files_to_record
from invenio_nrp.cli.records.metadata import read_metadata
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.records import RecordClient
from invenio_nrp.cli.base import run_async


@run_async
async def create_record(
        repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
        model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
        community: Annotated[Optional[str], typer.Option(help="Community name")] = None,
        workflow: Annotated[Optional[str], typer.Option(help="Workflow name")] = None,
        metadata: Annotated[Optional[str], typer.Argument(help="Metadata")] = None,
        metadata_only: Annotated[bool, typer.Option(help="The record will only have metadata")] = False,
        variable: Annotated[Optional[str], typer.Argument(help="Variable name")] = None,
        output: Annotated[
            Optional[Path], typer.Option("-o", help="Save the output to a file")
        ] = None,
        output_format: Annotated[
            Optional[OutputFormat],
            typer.Option("-f", help="The format of the output"),
        ] = None,
        files: Annotated[list[str], typer.Argument(help="List of files to upload")] = None,
):
    console = Console()

    metadata, files, variable = reorder_arguments(metadata, files, variable)
    if len(files) % 2 != 0:
        raise ValueError("Files must be in pairs of <path> and file metadata.")

    metadata = read_metadata(metadata)

    config = Config.from_file()
    client = AsyncClient(alias=repository, config=config)
    records_api: RecordClient = (
        client.user_records(model)
    )
    record = await records_api.create_record(metadata, community=community,
                                             workflow=workflow, files_enabled=not metadata_only)

    if variable:
        set_variable(config, variable, record.links.self_)

    # upload files
    await upload_files_to_record(record, files)

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.output(record)


def reorder_arguments(metadata, files, variable):
    # metadata are always ok
    files_variable = [
        variable,
        *files
    ]
    variable = None
    files = []
    for fv in files_variable:
        if not fv:
            continue
        if fv.startswith("@"):
            if variable:
                raise ValueError("Only one variable can be defined.")
            variable = fv
        else:
            files.append(fv)
    return metadata, files, variable