#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Memory-based data source.

This file is just a compatibility layer for the synchronous client.
"""

from io import BytesIO

MemoryReader = BytesIO
