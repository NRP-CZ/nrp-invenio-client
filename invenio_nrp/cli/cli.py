#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Main commandline client."""

from __future__ import annotations

import dataclasses
from typing import Callable, Optional

from typer import Typer

from invenio_nrp.cli.records import (
    create_record,
    download_record,
    get_record,
    scan_records,
    search_records,
    update_record,
)

from .files import download_files, list_files, update_file_metadata, upload_files
from .repositories import (
    add_repository,
    describe_repository,
    list_repositories,
    remove_repository,
    select_repository,
)
from .variables import get_variable, list_variables, remove_variable, set_variable

commands = [
    # verb centric
    ("add", "repository", add_repository),
    ("create", "record", create_record),
    ("describe", "repository", describe_repository),
    ("download", "record", download_record),
    ("download", "files", download_files),
    ("get", "record", get_record),
    ("get", "variable", get_variable),
    ("list", "files", list_files),
    ("list", "records", search_records),
    ("list", "repositories", list_repositories),
    ("list", "variables", list_variables),
    ("remove", "repository", remove_repository),
    ("remove", "variable", remove_variable),
    ("scan", "records", scan_records),
    ("search", "records", search_records),
    ("select", "repository", select_repository),
    ("set", "variable", set_variable),
    ("upload", "file", upload_files),
    ("update", "record", update_record),
    ("update", "file", update_file_metadata),
    # noun centric
    ("files", "list", list_files),
    ("files", "download", download_files),
    ("files", "upload", upload_files),
    ("files", "update", update_file_metadata),
    ("records", "create", create_record),
    ("records", "download", download_record),
    ("records", "get", get_record),
    ("records", "list", search_records),
    ("records", "search", search_records),
    ("records", "scan", scan_records),
    ("records", "update", update_record),
    ("repositories", "add", add_repository),
    ("repositories", "describe", describe_repository),
    ("repositories", "remove", remove_repository),
    ("repositories", "select", select_repository),
    ("repositories", "list", list_repositories),
    ("variables", "get", get_variable),
    ("variables", "set", set_variable),
    ("variables", "remove", remove_variable),
    ("variables", "list", list_variables),
]
"""CLI commands."""


@dataclasses.dataclass
class CommandTreeNode:
    """A tree of command groups/commands."""

    children: dict[str, CommandTreeNode] = dataclasses.field(default_factory=dict)
    """Child nodes of this group."""
    command: Optional[Callable[..., None]] = None
    """Command to execute at this node, if the children are empty."""

    def register_commands(self, parent_typer_group: Typer) -> None:
        """Register the commands to parent's typer group."""
        for child_name, child in self.children.items():
            if child.children:
                grp = Typer()
                child.register_commands(grp)
                parent_typer_group.add_typer(grp, name=child_name)
            else:
                parent_typer_group.command(child_name)(child.command)

    def add_command(
        self,
        command_decl: tuple[Callable[..., None]]
        | tuple[str, Callable[..., None]]
        | tuple[str, str, Callable[..., None]],
    ) -> None:
        """Add a command to the tree."""
        if len(command_decl) == 1:
            command = command_decl[0]
            assert not self.command, f"Can not set {command} to node {self}"
            assert not self.children, f"Can not set {command} to node {self}"
            self.command = command
        else:
            command_name = command_decl[0]
            assert isinstance(command_name, str), f"Invalid command name {command_name}"
            if command_name not in self.children:
                self.children[command_name] = CommandTreeNode()
            self.children[command_name].add_command(
                command_decl[1:],
            )


def generate_typer_command() -> Typer:
    """Register all commands into the typer app."""
    app = Typer()

    tree_root = CommandTreeNode()
    for cmd in commands:
        # ignore type as mypy says that the function can not be cast to Callable[..., None]
        tree_root.add_command(cmd)  # type: ignore

    tree_root.register_commands(app)

    return app


app = generate_typer_command()
"""Typer main application."""


if __name__ == "__main__":
    # call the application if run as a script
    app()
