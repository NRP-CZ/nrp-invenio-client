#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Commandline client for updating metadata of files."""

from typing import Optional

import typer
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.records.metadata import read_metadata


@run_async
async def update_file_metadata(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    key: Annotated[str, typer.Argument(help="Key for the file")],
    metadata: Annotated[
        Optional[str], typer.Argument(help="Metadata for the file")
    ] = None,
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name")] = None,
    published: Annotated[
        bool, typer.Option(help="Include only published records")
    ] = True,
    draft: Annotated[bool, typer.Option(help="Include only drafts")] = False,
) -> None:
    """Update the metadata of a file in a record."""
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
    record, record_id, repository_config = await read_record(
        record_id, repository, config, False, model, published
    )

    metadata = metadata or "{}"
    metadata_json = read_metadata(metadata)
    assert isinstance(metadata_json, dict), "Metadata must be a dictionary."

    if key:
        metadata_json["key"] = key
    files = await record.files().list()
    file = next((f for f in files.entries if f.key == key), None)
    if not file:
        raise ValueError(
            f"File with key {key} not found in record {record_id}: {", ".join([f.key for f in files.entries])}"
        )

    file.metadata = metadata_json
    await file.save()
