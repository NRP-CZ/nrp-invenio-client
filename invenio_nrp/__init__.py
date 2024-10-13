#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""API and commandline client for invenio repositories."""

from .client import SyncClient
from .config import Config

# from .shortcuts import get_records, get_records_sync

__all__ = (
    "Config",
    "SyncClient",
    # "get_records",
    # "get_records_sync",
)
