#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#

import requests.auth
from yarl import URL

from invenio_nrp.client.async_client.connection.auth import BearerTokenForHost


class BearerAuthentication(requests.auth.AuthBase):
    def __init__(self, tokens: list[BearerTokenForHost]):
        self.tokens = tokens

    def __call__(self, r):
        url = URL(r.url)

        for token in self.tokens:
            if url.host == token.host_url.host and url.scheme == token.host_url.scheme:
                r.headers["Authorization"] = f"Bearer {token.token}"
                break
        return r
