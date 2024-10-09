#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from rich import box
from rich.table import Table

from invenio_nrp.cli.base import format_table_value
from invenio_nrp.client.async_client.records import RecordList
from invenio_nrp.client.async_client.rest import BaseRecord


def format_search_table(record_list: RecordList[BaseRecord]):
    table = Table(
        title="Records", box=box.SIMPLE, title_justify="left", show_header=False
    )
    table.add_row("Self", str(record_list.links.self_))
    table.add_row("Next", str(record_list.links.next))
    table.add_row("Previous", str(record_list.links.prev))
    table.add_row("Total", str(record_list.total))
    yield table

    record: BaseRecord
    for record in record_list:
        yield from format_record_table(record)


def format_record_table(record: BaseRecord):
    table = Table(f"Record {record.id}", box=box.SIMPLE, title_justify="left")
    record_dump = record.model_dump()
    for k, v in record_dump.items():
        if k != "metadata":
            format_table_value(table, k, v)
    if "metadata" in record_dump:
        table.add_row("Metadata", "")
        for k, v in record_dump["metadata"].items():
            format_table_value(table, k, v, prefix="    ")
    yield table
