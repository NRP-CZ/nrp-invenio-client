#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Transfer protocols."""

from typing import Protocol

from ...connection import Connection
from ..files import File
from ..source import DataSource


class Transfer(Protocol):
    """Protocol for transferring files to the repository."""

    async def prepare(
        self, connection: Connection, files_link: str, transfer_payload: dict
    ) -> None:
        """Prepare the transfer.

        :param connection:              connection to the repository
        :param files_link:              link where the files are to be uploaded
        :param transfer_payload:        extra payload for the transfer, might be freely modified by this method
        """
        ...

    async def upload(
        self,
        connection: Connection,
        initialized_upload: File,
        file: DataSource,
    ) -> None:
        """Upload the file

        :param connection:              connection to the repository
        :param initialized_upload:      initialized upload as returned from the repository
        :param file:                    file to be uploaded
        """
        ...

    async def get_commit_payload(self, initialized_upload: File) -> dict:
        """Finalize the successful upload. There is no method to discard an unsuccessful upload,
        just use the "delete" operation on the failed file.

        :param initialized_upload:      initialized upload as returned from the repository
        :return:                        metadata of the upload as returned from the repository
        """
        ...
