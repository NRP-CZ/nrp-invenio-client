#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Clients (async/sync) for the NRP Invenio API."""

from .async_client import AsyncClient
from .sync_client import SyncClient

__all__ = ("SyncClient", "AsyncClient")
