#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Self

from pydantic import BaseModel, Field
from yarl import URL

from .repository import RepositoryConfig
from .variables import Variables


class Config(BaseModel):
    """
    The configuration of the NRP client as stored in the configuration file.
    """

    repositories: List[RepositoryConfig] = Field(default_factory=list)
    """Locally known repositories."""

    default_alias: Optional[str] = None
    """The alias of the default repository"""

    per_directory_variables: bool = True
    """Whether to load variables from a .nrp directory in the current directory.
       If set to False, the variables are loaded from the global configuration file
       located in ~/.nrp/variables.json.
    """

    _config_file_path: Optional[Path] = None
    """The path from which the config file was loaded."""

    class Config:
        extra = "forbid"

    @classmethod
    def from_file(cls, config_file_path: Optional[Path] = None) -> Self:
        """Load the configuration from a file."""
        if not config_file_path:
            if "NRP_CMD_CONFIG_PATH" in os.environ:
                config_file_path = Path(os.environ["NRP_CMD_CONFIG_PATH"])
            else:
                config_file_path = Path.home() / ".nrp" / "invenio-config.json"

        if config_file_path.exists():
            ret = cls.model_validate_json(
                config_file_path.read_text(encoding="utf-8"), strict=True
            )
        else:
            ret = cls()
        ret._config_file_path = config_file_path
        return ret

    def save(self, path: Optional[Path] = None):
        """Save the configuration to a file, creating parent directory if needed."""
        if path:
            self._config_file_path = path
        else:
            path = self._config_file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=4, by_alias=True),
            encoding="utf-8",
        )

    #
    # Repository management
    #

    def get_repository(self, alias: str) -> RepositoryConfig:
        for repo in self.repositories:
            if repo.alias == alias:
                return repo
        raise KeyError(f"Repository with alias '{alias}' not found")

    @property
    def default_repository(self) -> RepositoryConfig:
        return self.get_repository(self.default_alias)

    def add_repository(self, repository: RepositoryConfig):
        self.repositories.append(repository)

    def remove_repository(self, repository: RepositoryConfig | str):
        if isinstance(repository, str):
            repository = self.get_repository(repository)
        self.repositories.remove(repository)

    def set_default_repository(self, alias: str):
        try:
            next(repo for repo in self.repositories if repo.alias == alias)
        except StopIteration:
            raise ValueError(f"Repository with alias '{alias}' not found")
        self.default_alias = alias

    def get_repository_from_url(self, record_url: str | URL):
        record_url = URL(record_url)
        repository_root_url = record_url.with_path("/")
        for repository in self.repositories:
            if repository.url == repository_root_url:
                return repository
        # use info endpoint to find the repository
        return RepositoryConfig(
            alias=str(repository_root_url),
            url=repository_root_url,
            info=None,
        )

    def load_variables(self) -> Variables:
        if self.per_directory_variables:
            return Variables.from_file(Path.cwd() / ".nrp" / "variables.json")
        return Variables.from_file()