#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from pathlib import Path

import pytest
from yarl import URL

from invenio_nrp.config import Config, RepositoryConfig

pytest_plugins = ("pytest_asyncio",)

import logging

logging.basicConfig(level=logging.ERROR)


@pytest.fixture(scope="session")
def nrp_repository_config():
    tmp_config_file = Path("/tmp/.test-nrp-config.json")
    if tmp_config_file.exists():
        tmp_config_file.unlink()

    config = Config.from_file(tmp_config_file)
    config.add_repository(
        RepositoryConfig(
            alias="local",
            url=URL("https://127.0.0.1:5000"),
            token=(Path(__file__).parent / "test-repository" / "repo" / ".token_a")
            .read_text()
            .strip(),
            verify_tls=False,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    config.add_repository(
        RepositoryConfig(
            alias="zenodo",
            url=URL("https://www.zenodo.org"),
            token=None,
            verify_tls=True,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    config.save()
    return config
