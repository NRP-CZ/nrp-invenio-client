#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Command line interface for getting records."""

from __future__ import annotations

from pathlib import Path  # noqa
from typing import TYPE_CHECKING, Optional

import typer  # noqa
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.repository_requests.table_formatter import format_request_table
from invenio_nrp.config import Config

if TYPE_CHECKING:
    from invenio_nrp.client.async_client.request_types import RequestType


@run_async
async def create_request(
    request_type_id: Annotated[str, typer.Argument(help="Request type ID")],
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
        record_id, repository, config, False, model, published
    )

    request_types = await record.requests().applicable()
    request_type: RequestType | None = next(
        (rt for rt in request_types.hits if rt.type_id == request_type_id), None
    )
    if not request_type:
        raise ValueError(f"Request type {request_type_id} not found.")

    request = await request_type.create({}, submit=True)

    with OutputWriter(output, output_format, console, format_request_table) as printer:
        printer.output(request)
