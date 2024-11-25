#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""A source of data to upload to the repository."""

from .base import DataSource
from .file import FileDataSource
from .memory import MemoryDataSource

__all__ = ["DataSource", "FileDataSource", "MemoryDataSource"]
