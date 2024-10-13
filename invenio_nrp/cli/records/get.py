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

import requests
import typer
from rich.console import Console
from typing_extensions import Annotated
from yarl import URL

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.record_file_name import create_output_file_name
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.records import Record, RecordClient
from invenio_nrp.client.doi import resolve_doi
from invenio_nrp.config import RepositoryConfig


@run_async
async def get_record(
    record_ids: Annotated[list[str], typer.Argument(help="Record ID")],
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
) -> None:
    """Get a record from the repository."""
    console = Console()
    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    for rec_id in record_ids:
        if rec_id.startswith("@"):
            ids.extend(variables[rec_id[1:]])
        else:
            ids.append(rec_id)

    # TODO: run this in parallel
    for record_id in ids:
        await get_single_record(
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


async def get_single_record(
    record_id: str,
    console: Console,
    config: Config,
    repository: str | None,
    model: str | None,
    output: Path | None,
    output_format: OutputFormat | None,
    published: bool,
    draft: bool,
    expand: bool,
) -> tuple[Record, Path | None, RepositoryConfig]:
    """Get a single record from the repository and print/save it."""
    record, record_id, repository_config = await read_record(
        record_id, repository, config, expand, model, published
    )

    if output:
        output = create_output_file_name(
            output, str(record.id or record_id or "unknown_id"), record, output_format
        )
    if output and output.parent:
        output.parent.mkdir(parents=True, exist_ok=True)

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.output(record)

    return record, output, repository_config


async def read_record(
    record_id: str,
    repository: str | None,
    config: Config,
    expand: bool,
    model: str | None,
    published: bool,
) -> tuple[Record, str, RepositoryConfig]:
    """Read a record from the repository, returning the record, its id and the repository config."""
    record_id, repository_config = get_repository_from_record_id(
        record_id, config, repository
    )
    # set it temporarily to the config
    config.add_repository(repository_config)
    client = AsyncClient(config=config, alias=repository_config.alias)
    records_api: RecordClient = (
        client.published_records(model) if published else client.user_records(model)
    )
    record = await records_api.read_record(record_id=record_id, expand=expand)
    return record, record_id, repository_config


def get_repository_from_record_id(
    record_id: str, config: Config, repository: str | None = None
) -> tuple[str, RepositoryConfig]:
    """Try to get a repository from the record id.

    :param record_id: The record id (might be id, url, doi)
    :param config: The configuration of known repositories
    :param repository: The optional repository alias to use. If not passed in, the call will try to
                          resolve the repository from the record id.
    """
    if record_id.startswith("doi:"):
        record_id = resolve_doi(record_id[4:])
    elif record_id.startswith("https://doi.org/"):
        record_id = resolve_doi(record_id[len("https://doi.org/") :])

    if repository:
        repository_config = config.get_repository(repository)
        return record_id, repository_config

    if not record_id.startswith("https://"):
        return record_id, config.default_repository

    repository_config = config.get_repository_from_url(record_id)

    # if it is an api path, return it as it is
    record_url = URL(record_id)
    if record_url.path.startswith("/api/"):
        return str(record_id), repository_config

    # try to head the record to get the id
    resp = requests.head(
        str(record_url), allow_redirects=True, verify=repository_config.verify_tls
    )
    resp.raise_for_status()
    api_url = resp.links.get("linkset", {}).get("url")
    if api_url:
        return api_url, repository_config
    else:
        return str(record_url), repository_config
