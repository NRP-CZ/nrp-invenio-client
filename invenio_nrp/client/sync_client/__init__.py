#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Synchronous client for the NRP Invenio repository.

Provides the SyncClient class
that allows to interact with the NRP Invenio repository.

Use the synchronous client if you want to have an ease of use experience and you
are not expecting to download large files or make many requests in parallel.

Example usage:

.. code-block:: python
from invenio_nrp.client import SyncClient

client = SyncClient()

my_records = client.user_records()
for record in my_records.search():
    print(record.id)
"""

from .base import SyncClient

__all__ = ("SyncClient",)
