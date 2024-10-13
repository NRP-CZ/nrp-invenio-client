#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline interface for creating records."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async, set_variable
from invenio_nrp.cli.files.upload import upload_files_to_record
from invenio_nrp.cli.records.metadata import read_metadata
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient

if TYPE_CHECKING:
    from invenio_nrp.client.async_client.records import RecordClient


@run_async
async def create_record(
    metadata: Annotated[str, typer.Argument(help="Metadata")],
    files: Annotated[list[str], typer.Argument(help="List of files to upload")],
    variable: Annotated[Optional[str], typer.Argument(help="Variable name")],
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    community: Annotated[Optional[str], typer.Option(help="Community name")] = None,
    workflow: Annotated[Optional[str], typer.Option(help="Workflow name")] = None,
    metadata_only: Annotated[
        bool, typer.Option(help="The record will only have metadata")
    ] = False,
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Save the output to a file")
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("-f", help="The format of the output"),
    ] = None,
) -> None:
    """Create a new record in the repository and optionally upload files to it."""
    console = Console()

    metadata, files, variable = reorder_arguments(metadata, files, variable)
    if len(files) % 2 != 0:
        raise ValueError("Files must be in pairs of <path> and file metadata.")

    metadata_json = read_metadata(metadata)
    assert isinstance(metadata_json, dict), "Metadata must be a dictionary."

    config = Config.from_file()
    client = AsyncClient(alias=repository, config=config)
    records_api: RecordClient = client.user_records(model)
    record = await records_api.create_record(
        metadata_json,
        community=community,
        workflow=workflow,
        files_enabled=not metadata_only,
    )

    if variable:
        set_variable(config, variable, str(record.links.self_))

    # upload files
    await upload_files_to_record(record, *zip(files[::2], files[1::2]))

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.output(record)


def reorder_arguments(
    metadata: str, files: list[str], variable: str | None
) -> tuple[str, list[str], str | None]:
    """Reorder the arguments to have metadata, files and variable in the right order as they can be missing on cmdline.

    :param metadata:
    :param files:
    :param variable:
    :return:
    """
    # metadata are always ok
    files_variable = [variable, *files]
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
