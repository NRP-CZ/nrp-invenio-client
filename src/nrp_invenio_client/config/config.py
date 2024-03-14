import dataclasses
from io import StringIO
from pathlib import Path
from typing import List, Optional

import dacite
import yaml

from .repository_config import RepositoryConfig

serialization_config = dacite.Config()
serialization_config.type_hooks = {
    Path: lambda x: Path(x),
}


@dataclasses.dataclass
class NRPConfig:
    repositories: List[RepositoryConfig] = dataclasses.field(default_factory=list)
    default_repository: Optional[str] = None

    config_file = Path("~/.nrp/cmd-config.yaml").expanduser()

    def load(self, config_file=None):
        if not config_file:
            config_file = self.config_file
        else:
            config_file = Path(config_file)

        if not config_file.exists():
            return

        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        loaded = dacite.from_dict(
            type(self),
            config_data,
            serialization_config,
        )

        self.repositories = loaded.repositories
        self.default_repository = loaded.default_repository

    def save(self):
        if self.config_file.exists():
            previous_config_data = self.config_file.read_text().strip()
        else:
            previous_config_data = None

        io = StringIO()
        dict_data = dataclasses.asdict(self)
        dict_data.pop("config_file", None)
        yaml.safe_dump(dict_data, io)
        current_data = io.getvalue().strip()

        if previous_config_data != current_data:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self.config_file.write_text(current_data)

    def get_repository_config(self, alias=None):
        if alias is None:
            alias = self.default_repository

        for repo in self.repositories:
            if repo.alias == alias:
                return repo

        raise ValueError(f"Repository with alias '{alias}' not found")
