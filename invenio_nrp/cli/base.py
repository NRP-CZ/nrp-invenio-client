#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import enum
import inspect
import json
from asyncio import run as asyncio_run
from functools import wraps

import yaml
from rich.console import Console


class OutputFormat(enum.Enum):
    """Output format."""

    JSON = "json"
    JSON_LINES = "jsonl"
    YAML = "yaml"
    TABLE = "table"

    def __str__(self):
        return self.value


def format_output(output_format: OutputFormat, data):
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    match output_format:
        case OutputFormat.JSON:
            return json.dumps(data, indent=4)
        case OutputFormat.JSON_LINES:
            return json.dumps(
                data, ensure_ascii=False, separators=(",", ":"), indent=None
            ).replace("\n", "\\n")
        case OutputFormat.YAML:
            return yaml.safe_dump(data)
        case _:
            raise ValueError(f"Unknown output format: {output_format}")


def format_table_column_value(value):
    if isinstance(value, list):
        if all(isinstance(x, dict) for x in value):
            return ",\n".join(
                json.dumps(x, indent=2, ensure_ascii=False) for x in value
            )
        return ", ".join(str(x) for x in value)
    if isinstance(value, dict):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def format_table_value(table, k, v, prefix=""):
    if isinstance(v, dict):
        table.add_row(prefix + k, "")
        for k1, v1 in v.items():
            table.add_row(prefix + "    " + k1, format_table_column_value(v1))
    else:
        table.add_row(prefix + k, format_table_column_value(v))


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio_run(func(*args, **kwargs))

    return wrapper


def set_variable(config, name, value):
    if not isinstance(value, list):
        value = [value]

    variables = config.load_variables()

    if name.startswith("@"):
        name = name[1:]
    if name.startswith("+"):
        name = name[1:]
        variables[name] = variables.get(name, []) + value
    else:
        variables[name] = value
    variables.save()


class OutputWriter:
    def __init__(self, output_file, output_format, console, table_maker):
        self.output_file = output_file
        self.output_format = output_format
        self.console = console
        self.table_maker = table_maker
        self._stream = None
        self._multiple = False
        self._output_encountered = False

    def __enter__(self):
        if self.output_file:
            self._stream = self.output_file.open("w")
            if not hasattr(self._stream, "print"):

                def _print(data=None, end="\n"):
                    if data is not None:
                        self._stream.write(str(data))
                    self._stream.write(end)

                self._stream.print = _print
        else:
            self._stream = self.console
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._multiple and self.output_format == OutputFormat.JSON:
            self._stream.print("]")
        if self.output_file and self._stream:
            self._stream.close()
            self._stream = None

    def output(self, data: any):
        if self._multiple and self._output_encountered:
            match self.output_format:
                case OutputFormat.JSON:
                    self._stream.print(",")
                case OutputFormat.JSON_LINES:
                    self._stream.print()
                case OutputFormat.YAML:
                    self._stream.print("\n---")
                case _:
                    pass

        if self.output_format == OutputFormat.TABLE or self.output_format is None:
            if not isinstance(self._stream, Console):
                console = Console(file=self._stream)
            else:
                console = self._stream
            if inspect.isgeneratorfunction(self.table_maker):
                tables = list(self.table_maker(data))
            else:
                tables = self.table_maker(data)
                if not isinstance(tables, (tuple, list)):
                    tables = [tables]
            for table in tables:
                console.print(table)
        else:
            data = format_output(self.output_format, data)
            self._stream.print(data, end="" if self._multiple else "\n")
        self._output_encountered = True

    def multiple(self):
        self._multiple = True
        if self.output_format == OutputFormat.JSON:
            self._stream.print("[")
