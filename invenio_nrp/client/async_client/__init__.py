#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Asynchronous client for the NRP Invenio repository.

Provides the AsyncClient class
that allows to interact with the NRP Invenio repository asynchronously inside an
asyncio event loop.

Use the async client if you are developing an asynchronous application or you want
to make requests in parallel with other tasks.

The async client also contains a generic multi-chunk downloader to download multiple
files at once.

Example usage:

.. code-block:: python
from invenio_nrp import AsyncClient

client = AsyncClient()

my_records = client.user_records()
async for record in my_records.search():
    print(record.id)
"""

from .base import AsyncClient

__all__ = ("AsyncClient",)
