
import pytest

from invenio_nrp import SyncClient
from invenio_nrp.config import Config


@pytest.fixture
def saved_config_file(fs, nrp_repository_config: Config) -> Config:
    """Create a pre-filled config in a standard location.

    Using fs fixture to mock the location.
    """
    cfg = Config.from_file()
    cfg.repositories = nrp_repository_config.repositories
    cfg.save()
    return cfg

@pytest.fixture
def default_local(saved_config_file: Config) -> Config:
    """Set the default repository to 'local'."""
    saved_config_file.default_alias = "local"
    cli = SyncClient(config=saved_config_file, alias="local")
    cli.info(refresh=True)
    saved_config_file.save()
    return saved_config_file