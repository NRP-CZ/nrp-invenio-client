#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Low-level os support for files."""

import os
from io import IOBase
from pathlib import Path

type DataReader = IOBase
type DataWriter = IOBase


def open_file(_fpath: Path, mode: str) -> DataReader | DataWriter:
    """Open file."""
    r: DataReader | DataWriter = open(_fpath, mode=mode)  # type: ignore    # noqa: SIM115
    return r


def file_stat(_fpath: Path) -> os.stat_result:
    """Get file stats."""
    return os.stat(_fpath)


__all__ = (
    "DataReader",
    "DataWriter",
    "open_file",
    "file_stat",
)
