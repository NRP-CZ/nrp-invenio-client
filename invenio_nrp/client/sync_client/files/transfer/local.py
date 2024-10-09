#
# This file was generated from the asynchronous client at files/transfer/local.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from ...connection import Connection
from ..files import DataSource, File
from . import Transfer


class LocalTransfer(Transfer):
    """Local transfer. This transfer copies a local file to the repository.
    The file will be stored in repository's primary storage (thus local)
    and the upload will be handled solely through the repository.
    """

    def upload(
        self,
        connection: Connection,
        initialized_upload: File,
        file: DataSource,
    ) -> None:
        open_file = file.open()

        connection.put_stream(
            url=initialized_upload.links.content,
            file=open_file,
        )

    def prepare(
        self, connection: Connection, files_link: str, transfer_payload: dict
    ) -> None:
        pass

    def get_commit_payload(self, initialized_upload: File) -> dict:
        return {}
