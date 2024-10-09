#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated, Self

from invenio_nrp import Config
from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.get import get_repository_from_record_id
from invenio_nrp.cli.records.metadata import read_metadata
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient
from invenio_nrp.client.async_client.records import RecordClient


@run_async
async def update_record(
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    record_id: Annotated[str, typer.Argument(help="Record ID")] = None,
    metadata: Annotated[str, typer.Argument(help="Metadata")] = None,
    replace: Annotated[
        bool, typer.Option("--replace/--merge", help="Replace or merge the metadata")
    ] = True,
    path: Annotated[
        Optional[str], typer.Option("--path", "-p", help="Path within the metadata")
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Save the output to a file")
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("-f", help="The format of the output"),
    ] = None,
):
    console = Console()
    config = Config.from_file()

    if record_id.startswith("@"):
        record_id = record_id[1:]
        record_id = config.load_variables()[record_id]
        if len(record_id) > 1:
            raise ValueError(f"Variable {record_id} is not a single record ID.")
        record_id = record_id[0]

    metadata = read_metadata(metadata)
    record_id, repository_config = get_repository_from_record_id(
        record_id, config, repository
    )

    client = AsyncClient(repository=repository, config=config)
    records_api: RecordClient = client.user_records()
    record = await records_api.read_record(record_id=record_id)

    record.metadata = merge_metadata(record.metadata, metadata, replace, path)

    record = await record.update()

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.output(record)


def merge_metadata(old_metadata, new_metadata, replace, path):
    setters = InPathMDSetter.from_path(old_metadata, path)

    old = setters[-1].value
    if replace:
        if isinstance(old, dict):
            old.clear()
            old.update(new_metadata)
        elif isinstance(old, list):
            old.clear()
            old.extend(new_metadata)
        else:
            old = new_metadata
    else:
        if isinstance(old, dict):
            deep_merge(old, new_metadata)
        elif isinstance(old, list):
            old.extend(new_metadata)
        else:
            old = new_metadata
    setters[-1].value = old
    return setters[0].value


class InPathMDSetter:
    def __init__(self, metadata, parent: "Self" = None, parent_key=None):
        self.metadata = metadata
        self.parent = parent
        self.parent_key = parent_key

    @classmethod
    def from_path(cls, metadata, path):
        if path:
            path = path.split(".")
        else:
            path = []
        path = [x for x in path if x]
        ret = [cls(metadata)]
        for key_idx, key in enumerate(path):
            empty_factory = lambda: None
            if key_idx < len(path) - 1:
                next_key = path[key_idx + 1]
                if next_key.isdigit():
                    empty_factory = list
                else:
                    empty_factory = dict
            ret.append(ret[-1]._get_key(key, empty_factory))
        return ret

    def _get_key(self, key, empty_factory) -> "Self":
        if isinstance(self.metadata, dict):
            if key not in self.metadata:
                return InPathMDSetter(empty_factory(), self, key)
            return InPathMDSetter(self.metadata[key], self, key)
        elif isinstance(self.metadata, list):
            if int(key) >= len(self.metadata):
                return InPathMDSetter(empty_factory(), self, key)
            else:
                return InPathMDSetter(self.metadata[int(key)], self, key)
        else:
            raise ValueError(f"Cannot get key {key} from {self.metadata}")

    @property
    def value(self):
        return self.metadata

    @value.setter
    def value(self, value):
        self.metadata = value
        if self.parent:
            self.parent._set_key_in_parent(self.parent_key, self.metadata)

    def _set_key_in_parent(self, key, value):
        if isinstance(self.metadata, dict):
            self.metadata[key] = value
        elif isinstance(self.metadata, list):
            if int(key) < len(self.metadata):
                self.metadata[int(key)] = value
            else:
                self.metadata.append(value)
        else:
            raise ValueError(f"Cannot set key {key} in {self.metadata}")
        if self.parent:
            self.parent._set_key_in_parent(self.parent_key, self.metadata)


def deep_merge(old_md, new_md):
    if new_md is None:
        return None
    if isinstance(old_md, list):
        if isinstance(new_md, list):
            old_md.extend(new_md)
        else:
            old_md.append(new_md)
