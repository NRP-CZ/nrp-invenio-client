#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Command-line interface for searching records."""

from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async, set_variable
from invenio_nrp.cli.records.table_formatters import (
    format_record_table,
    format_search_table,
)
from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.records import RecordClient, RecordList
from invenio_nrp.config import Config


@run_async
async def search_records(
    query: Annotated[Optional[str], typer.Argument(help="Query string")] = None,
    variable: Annotated[Optional[str], typer.Argument(help="Variable name")] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    community: Annotated[Optional[str], typer.Option(help="Community name")] = None,
    size: Annotated[
        int, typer.Option(help="Number of results to return on a page")
    ] = 10,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    sort: Annotated[Optional[str], typer.Option(help="Sort order")] = "bestmatch",
    published: Annotated[
        bool, typer.Option("--published/--drafts", help="Include only published records")
    ] = True,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("--output-format", "-f", help="The format of the output"),
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Save the output to a file",
                                     click_type = click.Path(
                        file_okay=True,
                        writable=True,
                        resolve_path=True,
                        allow_dash=False,
                        path_type=Path,
                    ))
    ] = None,
) -> None:
    """Return a page of records inside repository that match the given query."""
    console = Console()
    config = Config.from_file()

    if query and query.startswith("@"):
        variable = query
        query = None

    records_api, args = await _prepare_search(
        community, config, model, page, published, query, repository, size, sort
    )

    record_list = await records_api.search(**args)

    if variable:
        urls = [str(record.links.self_) for record in record_list]
        set_variable(config, variable, urls)

    with OutputWriter(output, output_format, console, format_search_table) as printer:
        del record_list.aggregations
        printer.output(record_list)


async def _prepare_search(
    community: str | None,
    config: Config,
    model: str | None,
    page: int,
    published: bool,
    query: str | None,
    repository: str | None,
    size: int,
    sort: str | None,
) -> tuple[RecordClient, dict]:
    """Prepare the search for records."""
    client = AsyncClient(alias=repository, config=config)
    records_api: RecordClient = (
        client.published_records(model) if published else client.user_records(model)
    )
    args = {}
    if community:
        args["community"] = community
    if sort:
        args["sort"] = sort
    if query:
        args["q"] = query
    if page is not None:
        args["page"] = str(page)
    if size is not None:
        args["size"] = str(size)
    if not published:
        args["status"] = "draft"
    return records_api, args


@run_async
async def scan_records(
    query: Annotated[Optional[str], typer.Argument(help="Query string")] = None,
    variable: Annotated[Optional[str], typer.Argument(help="Variable name")] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    community: Annotated[Optional[str], typer.Option(help="Community name")] = None,
    size: Annotated[
        int, typer.Option(help="Number of results to return on a page")
    ] = 50,
    drafts: Annotated[bool, typer.Option(help="Include only drafts")] = False,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("--output-format", "-f", help="The format of the output"),
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Save the output to a file",
                                     click_type = click.Path(
                        file_okay=True,
                        writable=True,
                        resolve_path=True,
                        allow_dash=False,
                        path_type=Path,
                    ))
    ] = None,
) -> None:
    """Return all records inside repository that match the given query."""
    console = Console()
    config = Config.from_file()

    if query and query.startswith("@"):
        variable = query
        query = None

    records_api, args = await _prepare_search(
        community,
        config,
        drafts,
        model,
        1,
        published,
        query,
        repository,
        size,
        "oldest",
    )

    urls = set()
    last_created = None

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.multiple()

        while True:
            record_list: RecordList = await records_api.search(**args)
            new_entry_seen = False

            for entry in record_list:
                link = str(entry.links.self_)
                if link not in urls:
                    printer.output(entry)
                    urls.add(link)
                    last_created = entry.created.isoformat()
                    new_entry_seen = True
            if not new_entry_seen:
                break
            if query:
                args["q"] = f'created:["{last_created}" TO *] AND ({query})'
            else:
                args["q"] = f'created:["{last_created}" TO *]'

    if variable:
        set_variable(config, variable, list(urls))
