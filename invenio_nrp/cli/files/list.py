#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline client for files."""

from functools import partial
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.files.table_formatters import format_files_table
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.records.record_file_name import create_output_file_name


@run_async
async def list_files(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Save the output to a file")
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("-f", help="The format of the output"),
    ] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
) -> None:
    """Commandline client for listing files."""
    console = Console()
    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    if record_id.startswith("@"):
        ids.extend(variables[record_id[1:]])
    else:
        ids.append(record_id)

    # TODO: run this in parallel
    for record_id in ids:
        record, record_id, repository_config = await read_record(
            record_id, repository, config, False, model, published
        )
        files = await record.files().list()

        if output:
            output = create_output_file_name(
                output, str(record.id), record, output_format
            )
            if output.parent:
                output.parent.mkdir(parents=True, exist_ok=True)

        with OutputWriter(
            output, output_format, console, partial(format_files_table, record)
        ) as printer:
            printer.output(files)
