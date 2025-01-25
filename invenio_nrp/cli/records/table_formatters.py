#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Table formatters for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from rich import box
from rich.table import Table

from invenio_nrp.cli.base import write_table_row
from invenio_nrp.converter import converter

if TYPE_CHECKING:
    from invenio_nrp.client.async_client.records import Record, RecordList


def format_search_table(data: RecordList) -> Generator[Table, None, None]:
    """Format a search result as a table."""
    table = Table(
        title="Records", box=box.SIMPLE, title_justify="left", show_header=False
    )
    table.add_row("Self", str(data.links.self_))
    table.add_row("Next", str(data.links.next))
    table.add_row("Previous", str(data.links.prev))
    table.add_row("Total", str(data.total))
    yield table

    for record in data:
        yield from format_record_table(record)


def format_record_table(
    data: Record,
    **kwargs: Any,  # noqa: ANN401
) -> Generator[Table, None, None]:
    """Format a record as a table."""
    table = Table(f"Record {data.id}", box=box.SIMPLE, title_justify="left")
    record_dump = converter.unstructure(data)
    for k, v in record_dump.items():
        if k != "metadata":
            write_table_row(table, k, v)
    if "metadata" in record_dump:
        table.add_row("Metadata", "")
        for k, v in record_dump["metadata"].items():
            write_table_row(table, k, v, prefix="    ")
    yield table
