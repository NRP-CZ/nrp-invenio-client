#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Formatter for request and request types tables."""

from typing import Generator

from rich import box
from rich.table import Table

from invenio_nrp.cli.base import write_table_row
from invenio_nrp.client.async_client.request_types import RequestType
from invenio_nrp.client.async_client.requests import Request


def format_request_table(data: Request) -> Generator[Table, None, None]:
    """Format request table both for requests and request types."""
    table = Table(
        title="Request", box=box.SIMPLE, title_justify="left", show_header=False
    )
    write_table_row(table, "id", data.id)
    write_table_row(table, "status", data.status)
    write_table_row(table, "type", data.type)
    write_table_row(table, "created", data.created)
    write_table_row(table, "updated", data.updated)
    write_table_row(table, "payload", data.payload)
    write_table_row(table, "links", data.links)
    yield table


def format_request_type_table(data: RequestType) -> Generator[Table, None, None]:
    """Format request type table."""
    table = Table(
        title="Request Type",
        box=box.SIMPLE,
        title_justify="left",
        show_header=False,
    )
    write_table_row(table, "id", data.type_id)
    write_table_row(table, "actions", data.links.actions)
    yield table


def format_request_and_types_table(data: dict) -> Generator[Table, None, None]:
    """Format request and request types table."""
    request: Request
    for request in data["requests"]:
        yield from format_request_table(request)

    request_type: RequestType
    for request_type in data["request_types"]:
        yield from format_request_type_table(request_type)
