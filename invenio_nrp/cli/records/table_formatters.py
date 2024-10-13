#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Table formatters for records."""

from typing import Generator

from rich import box
from rich.table import Table

from invenio_nrp.cli.base import write_table_row
from invenio_nrp.client.async_client.records import Record, RecordList


def format_search_table(record_list: RecordList) -> Generator[Table]:
    """Format a search result as a table."""
    table = Table(
        title="Records", box=box.SIMPLE, title_justify="left", show_header=False
    )
    table.add_row("Self", str(record_list.links.self_))
    table.add_row("Next", str(record_list.links.next))
    table.add_row("Previous", str(record_list.links.prev))
    table.add_row("Total", str(record_list.total))
    yield table

    for record in record_list:
        yield from format_record_table(record)


def format_record_table(record: Record) -> Generator[Table]:
    """Format a record as a table."""
    table = Table(f"Record {record.id}", box=box.SIMPLE, title_justify="left")
    record_dump = record.model_dump()  # type: ignore
    for k, v in record_dump.items():
        if k != "metadata":
            write_table_row(table, k, v)
    if "metadata" in record_dump:
        table.add_row("Metadata", "")
        for k, v in record_dump["metadata"].items():
            write_table_row(table, k, v, prefix="    ")
    yield table
