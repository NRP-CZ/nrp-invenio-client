#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import tempfile
from pathlib import Path

from yarl import URL

from invenio_nrp.config import RepositoryConfig


def test_config():
    from invenio_nrp.config.config import Config

    config = Config()
    assert config.repositories == []
    assert config.default_alias is None
    assert config._config_file_path is None

    config.add_repository(
        RepositoryConfig(
            alias="test",
            url=URL("https://example.com"),
            token="token",
            verify_tls=True,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    assert config.get_repository("test").alias == "test"

    with tempfile.NamedTemporaryFile() as f:
        config.save(Path(f.name))
        print(Path(f.name).read_text())
        loaded_config = Config.from_file(Path(f.name))

    print(config)
    print(loaded_config)

    assert loaded_config == config
