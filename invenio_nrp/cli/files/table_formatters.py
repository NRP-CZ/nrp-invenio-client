#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Table formatters for files."""

from typing import Generator

from rich import box
from rich.table import Table

from invenio_nrp.client.async_client.files import FilesList
from invenio_nrp.client.async_client.records import Record


def format_files_table(record: Record, files: FilesList) -> Generator[Table]:
    """Format the files table."""
    table = Table(
        "Key",
        "Status",
        "Mimetype",
        "Access",
        "Metadata",
        "Content URL",
        title=f"Files for record {record.id}",
        box=box.SIMPLE,
        title_justify="left",
    )
    for file in files.entries:
        table.add_row(
            file.key,
            file.status,
            file.mimetype,
            str(file.access),
            str(file.metadata),
            str(file.links.content),
        )
    yield table
