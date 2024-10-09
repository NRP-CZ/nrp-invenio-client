#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""A response that can raise parsed invenio errors."""
import json

from aiohttp import ClientResponse

from invenio_nrp.client.errors import (
    RepositoryClientError,
    RepositoryCommunicationError,
    RepositoryServerError,
)


class RepositoryResponse(ClientResponse):
    """
    A response that can raise parsed invenio errors.
    """

    async def raise_for_invenio_status(self) -> None:
        """
        Raises an exception if the response status code is not 2xx.

        :raises RepositoryServerError: if the status code is 5xx
        :raises RepositoryClientError: if the status code is 4xx
        :raises RepositoryCommunicationError: if the status code is not 2xx nor 4xx nor 5xx
        """
        if not self.ok:
            payload = await self.text()
            self.release()
            try:
                payload = json.loads(payload)
            except ValueError as e:
                payload = {
                    "status": self.status,
                    "reason": payload,
                }

            if self.status >= 500:
                raise RepositoryServerError(self.request_info, payload)
            elif self.status >= 400:
                raise RepositoryClientError(self.request_info, payload)
            raise RepositoryCommunicationError(self.request_info, payload)
