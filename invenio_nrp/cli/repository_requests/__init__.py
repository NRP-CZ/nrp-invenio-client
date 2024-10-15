#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""CLI for requests."""

from .create import create_request
from .list import list_requests

__all__ = ("list_requests", "create_request")
