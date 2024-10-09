#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import dataclasses
from typing import Callable, Dict, Optional, Tuple
from venv import create

from typer import Typer

from invenio_nrp.cli.records import (
    download_record,
    get_record,
    scan_records,
    search_records,
    create_record,
    update_record
)

from .repositories import (
    add_repository,
    describe_repository,
    list_repositories,
    remove_repository,
    select_repository,
)
from .variables import get_variable, list_variables, remove_variable, set_variable
from .files import list_files, download_files

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
    ("update", "record", update_record),
    # noun centric
    ("files", "list", list_files),
    ("files", "download", download_files),
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


@dataclasses.dataclass
class CommandTreeNode:
    children: Dict[str, CommandTreeNode] = dataclasses.field(default_factory=dict)
    command: Optional[Callable] = None

    def register_commands(self, parent: Typer):
        for child_name, child in self.children.items():
            if child.children:
                grp = Typer()
                child.register_commands(grp)
                parent.add_typer(grp, name=child_name)
            else:
                parent.command(child_name)(child.command)

    def add_command(self, command_decl: Tuple):
        if len(command_decl) == 1:
            command = command_decl[0]
            assert not self.command, f"Can not set {command} to node {self}"
            assert not self.children, f"Can not set {command} to node {self}"
            self.command = command
        else:
            command_name = command_decl[0]
            if command_name not in self.children:
                self.children[command_name] = CommandTreeNode()
            self.children[command_name].add_command(
                command_decl[1:],
            )


def generate_typer_command():
    import typer

    app = typer.Typer()

    tree_root = CommandTreeNode()
    for cmd in commands:
        tree_root.add_command(cmd)

    tree_root.register_commands(app)

    return app


app = generate_typer_command()

if __name__ == "__main__":
    app()