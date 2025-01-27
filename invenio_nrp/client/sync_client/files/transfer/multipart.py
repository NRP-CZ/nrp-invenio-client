#
# This file was generated from the asynchronous client at files/transfer/multipart.py by generate_synchronous_client.sh
# Do not edit this file directly, instead edit the original file and regenerate this file.
#


"""Local transfer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yarl import URL

from ...connection.aws_limits import adjust_upload_multipart_params
from . import Transfer

if TYPE_CHECKING:
    from yarl import URL

    from ...connection import Connection
    from ...streams import DataSource
    from ..files import File, MultipartUploadLinks


class MultipartTransfer(Transfer):
    """Local transfer.

    This transfer copies a local file to the repository.
    The file will be stored in repository's primary storage (thus local)
    and the upload will be handled solely through the repository.
    """

    def prepare(
        self,
        connection: Connection,
        files_link: URL,
        transfer_payload: dict,
        source: DataSource,
    ) -> None:
        """Prepare the transfer."""
        if not transfer_payload.get("size"):
            transfer_payload["size"] = source.size()

        transfer_md = transfer_payload.get("transfer", {})

        parts, part_size = adjust_upload_multipart_params(
            transfer_payload["size"],
            transfer_md.get("parts"),
            transfer_md.get("part_size"),
        )
        transfer_md["parts"] = parts
        transfer_md["part_size"] = part_size
        
    def upload(
        self,
        connection: Connection,
        initialized_upload: File,
        source: DataSource,
    ) -> None:
        """Upload the file."""
        links: list[MultipartUploadLinks] = initialized_upload.links.parts or []
        assert links

        number_of_parts = len(links)
        part_size: int = initialized_upload.transfer.part_size

        size = initialized_upload.size

        for pt in range(number_of_parts):
            start = pt * part_size
            count = min(part_size, size - start)
            connection.put_stream(
                url=links[pt].url,
                source=source,
                open_kwargs={"offset": start, "count": count},
                headers={
                    "Content-Length": str(count),
                    "Content-Type": "application/octet-stream",
                }
            )

    def get_commit_payload(self, initialized_upload: File) -> dict:
        """Get payload for finalization of the successful upload."""
        return {}

