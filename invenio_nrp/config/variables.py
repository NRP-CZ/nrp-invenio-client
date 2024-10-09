#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Variables(BaseModel):
    """
    Variables for the commandline tools.
    """

    variables: Dict[str, List[str]] = Field(default_factory=dict)

    _config_file_path: Optional[Path] = None

    class Config:
        extra = "forbid"

    @classmethod
    def from_file(cls, config_file_path: Optional[Path] = None) -> "Variables":
        """Load the configuration from a file."""
        if not config_file_path:
            config_file_path = Path.home() / ".nrp" / "variables.json"

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

    def __getitem__(self, key: str) -> List[str]:
        try:
            return self.variables[key]
        except KeyError:
            raise KeyError(f"Variable {key} not found at {self._config_file_path}")

    def __setitem__(self, key: str, value: List[str]):
        self.variables[key] = value

    def __delitem__(self, key: str):
        del self.variables[key]

    def get(self, key: str) -> Optional[List[str]]:
        return self.variables.get(key)

    def items(self):
        return self.variables.items()
