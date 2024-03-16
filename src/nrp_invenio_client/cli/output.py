import json
import sys
from typing import Any, Dict, Generator, Iterable, List

import yaml
from tabulate import tabulate


# taken from https://stackoverflow.com/a/66853182
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def print_output(
    data: List[Dict] | Dict, output_format="table", order: Dict[str, int] = None
):
    if not output_format:
        output_format = "table"
    if isinstance(data, list):
        print_list_output(data, output_format, order or {})
    elif isinstance(data, dict):
        print_dict_output(data, output_format, order or {})
    else:
        raise ValueError(f"Unknown data type for tabular output: {type(data)}")


def print_list_output(
    data: List[Dict], output_format="table", order: Dict[str, int] = None
):
    if not output_format:
        output_format = "table"
    if output_format == "json":
        print(json.dumps(sorted_data(data), indent=4, ensure_ascii=False))
    elif output_format == "yaml":
        print(
            yaml.dump(
                sorted_data(data),
                sort_keys=False,
                Dumper=NoAliasDumper,
                allow_unicode=True,
            )
        )
    elif output_format == "table":
        formatted_table = format_list_to_table(data, order)
        print(formatted_table)
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def print_dict_output(
    data: Dict,
    output_format: str = "table",
    order: Dict[str, int] = None,
    file=sys.stdout,
):
    if not output_format:
        output_format = "table"
    if output_format == "json":
        print(json.dumps(sorted_data(data), indent=4, ensure_ascii=False), file=file)
    elif output_format == "yaml":
        print(
            yaml.dump(
                sorted_data(data),
                sort_keys=False,
                Dumper=NoAliasDumper,
                allow_unicode=True,
            ),
            file=file,
        )
    elif output_format == "table":
        formatted_table = format_dict_to_table(data, order)
        print(formatted_table, file=file)
    elif output_format == "long":
        formatted_table = format_dict_to_long_table(data, order)
        print(formatted_table, file=file)
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def format_dict_to_table(data, order):
    header = list(data.keys())
    sort_header(header, order)
    table_data = [[stringify(data[key]) for key in header]]
    formatted_table = tabulate(table_data, headers=header)
    return formatted_table


def format_dict_to_long_table(data, order):
    table_data = [[key, stringify(data[key])] for key in data]
    table_data.sort()
    return tabulate(table_data, tablefmt="plain")


def format_list_to_table(data, order):
    header = list(data[0].keys())
    sort_header(header, order)
    table_data = [[stringify(row[key]) for key in header] for row in data]
    formatted_table = tabulate(table_data, headers=header)
    return formatted_table


def stringify(x):
    if isinstance(x, (tuple, list)):
        return "\n".join([str(stringify(y)) for y in x])
    if isinstance(x, dict):
        return tabulate([(k, stringify(v)) for k, v in x.items()], tablefmt="plain")
    return x


def sort_header(header, order):
    if order:
        sort_mapping = {x: order.get(x, idx) for idx, x in enumerate(header)}

        header.sort()


def print_output_list(
    data: Iterable[Dict] | Generator[Dict, Any, None], output_format: str
):
    if not output_format:
        output_format = "table"
    if output_format == "json":
        print("[")
    for idx, item in enumerate(data):
        if idx > 0:
            if output_format == "json":
                print(",")
            if output_format == "yaml":
                print("---")
        print_output(item, output_format)
    if output_format == "json":
        print("]")


def sorted_data(data):
    def key(x):
        return (
            {"mid": 0, "id": 1, "metadata": 100}.get(  # keep the metadata last
                x[0], 10
            ),
            x[0],
        )

    return dict(sorted(data.items(), key=key))
