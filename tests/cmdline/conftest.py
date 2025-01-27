
import copy
from collections.abc import Iterator

import pytest

from invenio_nrp import SyncClient
from invenio_nrp.config import Config


@pytest.fixture(scope="function")
def saved_config_file(clear_config, nrp_repository_config: Config) -> Config:
    """Create a pre-filled config in a standard location.

    Using fs fixture to mock the location.
    """
    cfg = Config.from_file()
    cfg.repositories = copy.deepcopy(nrp_repository_config.repositories)
    cfg.save()
    return cfg

@pytest.fixture(scope="function")
def default_local(saved_config_file: Config) -> Config:
    """Set the default repository to 'local'."""
    saved_config_file.default_alias = "local"
    cli = SyncClient(config=saved_config_file, alias="local")
    cli.info(refresh=True)
    saved_config_file.save()
    return saved_config_file

@pytest.fixture(scope="function")
def clear_config(fs) -> Iterator[None]:
    """Remove the config file."""
    path = Config.from_file()._config_file_path
    assert path
    if path.exists():
        path.unlink()
    try:
        yield
    finally:
        if path.exists():
            path.unlink()
    