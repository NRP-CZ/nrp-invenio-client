#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import os
from io import RawIOBase
from pathlib import Path

type DataReader = RawIOBase
type DataWriter = RawIOBase


def open_file(_fpath: Path, mode: str) -> DataReader | DataWriter:
    r: DataReader | DataWriter = open(_fpath, mode=mode)  # noqa
    return r


def file_stat(_fpath: Path) -> os.stat_result:
    return os.stat(_fpath)


__all__ = (
    "DataReader",
    "DataWriter",
    "open_file",
    "file_stat",
)
