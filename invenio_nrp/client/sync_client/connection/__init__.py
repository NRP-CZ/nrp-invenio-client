#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Synchronous client for the NRP Invenio repository - low level connection."""

from .connection import Connection

__all__ = ("Connection",)
