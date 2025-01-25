#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Local transfer."""

from yarl import URL

from ...connection import Connection
from ..files import DataSource, File
from . import Transfer


class LocalTransfer(Transfer):
    """Local transfer.

    This transfer copies a local file to the repository.
    The file will be stored in repository's primary storage (thus local)
    and the upload will be handled solely through the repository.
    """

    async def upload(
        self,
        connection: Connection,
        initialized_upload: File,
        file: DataSource,
    ) -> None:
        """Upload the file."""
        if not initialized_upload.links.content:
            raise ValueError("The upload does not provide the content link.")
        
        async with file.open() as open_file:  # type: ignore
            await connection.put_stream(
                url=initialized_upload.links.content,
                file=open_file,
            )

    async def prepare(
        self, connection: Connection, files_link: URL, transfer_payload: dict,
        file: DataSource
    ) -> None:
        """Prepare the transfer."""
        pass

    async def get_commit_payload(self, initialized_upload: File) -> dict:
        """Get payload for finalization of the successful upload."""
        return {}
