#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Command line client for updating records."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Type

import click
import typer
from deepmerge import always_merger
from rich.console import Console
from typing_extensions import Annotated, Self

from invenio_nrp.cli.base import OutputFormat, OutputWriter, run_async
from invenio_nrp.cli.records.get import get_repository_from_record_id
from invenio_nrp.cli.records.metadata import read_metadata
from invenio_nrp.cli.records.table_formatters import format_record_table
from invenio_nrp.client import AsyncClient
from invenio_nrp.config import Config

if TYPE_CHECKING:
    from invenio_nrp.client.async_client.records import RecordClient


@run_async
async def update_record(
    record_id: Annotated[str, typer.Argument(help="Record ID")],
    metadata: Annotated[str, typer.Argument(help="Metadata")],
    repository: Annotated[Optional[str], typer.Option(help="Repository alias")] = None,
    replace: Annotated[
        bool, typer.Option("--replace/--merge", help="Replace or merge the metadata")
    ] = True,
    path: Annotated[
        Optional[str], typer.Option("--path", "-p", help="Path within the metadata")
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("-o", help="Save the output to a file",
                                     click_type = click.Path(
                        file_okay=True,
                        writable=True,
                        resolve_path=True,
                        allow_dash=False,
                        path_type=Path,
                    ))
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option("-f", help="The format of the output"),
    ] = None,
) -> None:
    """Update a record with new metadata."""
    console = Console()
    config = Config.from_file()

    if record_id.startswith("@"):
        record_id = record_id[1:]
        loaded_record_ids = config.load_variables()[record_id]
        if len(loaded_record_ids) != 1:
            raise ValueError(
                f"Variable {record_id} is not a single record ID: {loaded_record_ids}"
            )
        record_id = loaded_record_ids[0]

    metadata_json = read_metadata(metadata)
    record_id, repository_config = get_repository_from_record_id(
        record_id, config, repository
    )

    client = AsyncClient(alias=repository, config=config)
    records_api: RecordClient = client.user_records()
    record = await records_api.read_record(record_id=record_id)

    record.metadata = merge_metadata_at_path(
        record.metadata, metadata_json, replace, path
    )

    record = await record.update()

    with OutputWriter(output, output_format, console, format_record_table) as printer:
        printer.output(record)


def merge_metadata_at_path(
    metadata: Any,  # noqa: ANN401
    new_metadata: Any,  # noqa: ANN401
    replace: bool,
    path: str | None,
) -> dict:
    """Merge metadata at a path in a nested dictionary/list.

    :param metadata:         the whole metadata into which the new metadata should be merged
    :param new_metadata:     the new metadata to merge at path `path`
    :param replace:          whether to replace the old metadata at the path or merge them
    :param path:             the path to the metadata to merge
    :return:                 modified metadata
    """
    setters = InPathMDSetter.from_path(metadata, path or "")

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
            always_merger.merge(old, new_metadata)
        elif isinstance(old, list):
            old.extend(new_metadata)
        else:
            old = new_metadata
    setters[-1].value = old
    return setters[0].value


class InPathMDSetter:
    """A class for setting metadata at a path in a nested dictionary/list."""

    def __init__(
        self,
        metadata: dict | list,
        parent: Self | None = None,
        parent_key: str | int | None = None,
    ):
        """Create a new InPathMDSetter object."""
        self.metadata = metadata
        self.parent = parent
        self.parent_key = parent_key

    @classmethod
    def from_path(cls, metadata: dict | list, path: str) -> list[Self]:
        """Create a list of InPathMDSetter objects representing the path to the metadata.

        Each object in the list represents a key in the path to the metadata with a getter
        and setter for the value at that key.
        """
        path_parts = path.split(".") if path else []
        path_parts = [x for x in path_parts if x]
        ret = [cls(metadata)]
        for key_idx, key in enumerate(path_parts):

            def empty_factory() -> None:
                return None

            if key_idx < len(path_parts) - 1:
                next_key = path_parts[key_idx + 1]
                empty_factory = list if next_key.isdigit() else dict
            ret.append(ret[-1]._get_key(key, empty_factory))
        return ret

    def _get_key(self, key: str, empty_factory: Callable) -> Self:
        cls: Type[Self] = type(self)
        if isinstance(self.metadata, dict):
            if key not in self.metadata:
                return cls(empty_factory(), self, key)
            return cls(self.metadata[key], self, key)
        elif isinstance(self.metadata, list):
            if int(key) >= len(self.metadata):
                return cls(empty_factory(), self, key)
            else:
                return cls(self.metadata[int(key)], self, key)
        else:
            raise ValueError(f"Cannot get key {key} from {self.metadata}")

    @property
    def value(self) -> Any:  # noqa: ANN401
        """Get the value of the metadata at the path represented by this object."""
        return self.metadata

    @value.setter
    def value(self, value: Any) -> None:  # noqa: ANN401
        """Set the value of the metadata at the path represented by this object."""
        self.metadata = value
        if self.parent:
            assert self.parent_key is not None
            self.parent._set_key_in_parent(self.parent_key, self.metadata)

    def _set_key_in_parent(self, key: str | int, value: Any) -> None:  # noqa: ANN401
        assert self.parent_key is not None
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
