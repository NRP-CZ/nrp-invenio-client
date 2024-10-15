#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import tempfile
from pathlib import Path

import pytest
from pydantic import BaseModel
from yarl import URL

from invenio_nrp.config import RepositoryConfig
from invenio_nrp.types.yarl_url import YarlURL


def test_url_parsing():
    class A(BaseModel):
        url: YarlURL

    assert isinstance(A(url="https://example.com").url, URL)
    with pytest.raises(ValueError, match="URL must be https"):
        A(url="http://example.com")


def test_config():
    from invenio_nrp.config.config import Config

    config = Config()
    assert config.repositories == []
    assert config.default_alias is None
    assert config._config_file_path is None

    config.add_repository(
        RepositoryConfig(
            alias="test",
            url="https://example.com",
            token="token",
            tls_verify=True,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    assert config.get_repository("test").alias == "test"

    with tempfile.NamedTemporaryFile() as f:
        config.save(Path(f.name))
        loaded_config = Config.from_file(Path(f.name))

    assert loaded_config == config
