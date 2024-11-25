#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Command line interface for getting records."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.repository_requests.table_formatter import (
    format_request_and_types_table,
)
from invenio_nrp.client.async_client.request_types import RequestType
from invenio_nrp.client.async_client.requests import Request
from invenio_nrp.config import Config


@run_async
async def list_requests(
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
    """Get a record from the repository."""
    console = Console()
    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    if record_id.startswith("@"):
        ids.extend(variables[record_id[1:]])
    else:
        ids.append(record_id)
    if len(ids) > 1:
        raise ValueError("Only one record id can be passed in.")
    record_id = ids[0]

    record, record_id, repository_config, record_client = await read_record(
        record_id, repository, config, True, model, published
    )

    with OutputWriter(
        output, output_format, console, format_request_and_types_table
    ) as printer:
        data = {
            "requests": [
                Request.model_validate(x) for x in record.expanded.get("requests", [])
            ],
            "request_types": [
                RequestType.model_validate(x)
                for x in record.expanded.get("request_types", [])
            ],
        }
        printer.output(data)
