#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""RDM info."""

from yarl import URL

from invenio_nrp.types import RepositoryInfo, RepositoryInfoLinks


def make_rdm_info(url: URL) -> RepositoryInfo:
    """If repository does not provide the info endpoint, we assume it is a plain invenio rdm."""
    return RepositoryInfo(
        name="RDM repository",
        description="",
        version="rdm",
        invenio_version="rdm",
        transfers=[
            "local-transfer",
        ],
        links=RepositoryInfoLinks(
            self_=url,
            records=url / "api" / "records/",
            user_records=url / "api" / "user" / "records/",
            requests=url / "api" / "requests/",
            models=None,
        ),
        models={},
    )
