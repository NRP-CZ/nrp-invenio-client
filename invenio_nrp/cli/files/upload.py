#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline client for uploading files."""

from pathlib import Path
from typing import Annotated, Any, Optional

import typer

from invenio_nrp.cli.base import run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.records.metadata import read_metadata
from invenio_nrp.client.async_client.records import Record
from invenio_nrp.client.async_client.streams import DataSource, StdInDataSource
from invenio_nrp.config import Config


async def upload_files_to_record(
    record: Record, *files: tuple[str | DataSource | Path, dict[str, Any] | str]
) -> None:
    """Upload files to a record."""
    # convert files to pairs
    for file, metadata in files:
        if not isinstance(metadata, dict):
            metadata_json = read_metadata(metadata)
        else:
            metadata_json = metadata

        key = metadata_json.get("key")
        if file == "-":
            file = StdInDataSource()
            key = key or "stdin"
        elif not key and isinstance(file, (str, Path)):
            key = Path(file).name
        if not key:
            raise ValueError("Key must be provided for file")

        # TODO: more efficient transfer of large/number of files in parallel here
        await record.files().upload(
            key,
            metadata_json,
            file,
        )


@run_async
async def upload_files(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    file: Annotated[str, typer.Argument(help="File to upload")],
    metadata: Annotated[
        Optional[str], typer.Argument(help="Metadata for the file")
    ] = None,
    key: Annotated[Optional[str], typer.Option(help="Key for the file")] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
) -> None:
    """Upload a file to a record."""
    config = Config.from_file()
    variables = config.load_variables()

    ids = []
    if record_id.startswith("@"):
        ids.extend(variables[record_id[1:]])
    else:
        ids.append(record_id)

    if len(ids) > 1:
        raise ValueError("Only one record ID can be provided")

    record_id = ids[0]
    record, record_id, repository_config, record_client = await read_record(
        record_id, repository, config, False, model, published
    )

    metadata = metadata or "{}"
    metadata_json = read_metadata(metadata)
    assert isinstance(metadata_json, dict), "Metadata must be a dictionary."
    if key:
        metadata_json["key"] = key
    await upload_files_to_record(record, (file, metadata_json))
