#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from invenio_nrp import Config
from invenio_nrp.cli.base import run_async
from invenio_nrp.cli.records.get import read_record
from invenio_nrp.cli.records.metadata import read_metadata


async def upload_files_to_record(record, files):
    # convert files to pairs
    files = zip(files[::2], files[1::2])
    for file, metadata in files:
        if not isinstance(metadata, dict):
            metadata = read_metadata(metadata)
        if file == "-":
            file = sys.stdin.buffer
            key = metadata.get("key", "stdin")
        else:
            key = metadata.get("key", Path(file).name)
        # TODO: more efficient transfer of large/number of files in parallel here
        await record.files().upload(
            key,
            metadata,
            file,
        )


@run_async
async def upload_files(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    file: Annotated[str, typer.Argument(help="File to upload")],
    metadata: Annotated[
        Optional[str], typer.Argument(help="Metadata for the file")
    ] = None,
    key: Annotated[str, typer.Option(help="Key for the file")] = None,
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

    if len(ids) > 1:
        raise ValueError("Only one record ID can be provided")

    record_id = ids[0]
    record, record_id, repository_config = await read_record(
        record_id, repository, config, False, model, published
    )

    metadata = metadata or "{}"
    metadata = read_metadata(metadata)
    if key:
        metadata["key"] = key
    await upload_files_to_record(record, [file, metadata])
