#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base types for invenio REST responses."""

import dataclasses
from datetime import datetime

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from yarl import URL

from .yarl_url import YarlURL


class Model(BaseModel):
    """Base pydantic model, which allows getting extra fields via normal dot operator."""

    class Config:  # noqa
        extra = "allow"

    def __getattr__(self, item: str) -> any:
        """Get extra fields from the model_extra attribute."""
        if self.model_extra:
            if item in self.model_extra:
                return self.model_extra[item]
            dash_item = item.replace("_", "-")
            if dash_item in self.model_extra:
                return self.model_extra[dash_item]
        return super().__getattr__(item)


JSONDateTime = Annotated[
    datetime,
    BeforeValidator(lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x),
]
"""Python pydantic-enabled datetime."""


@dataclasses.dataclass
class URLBearerToken:
    """URL and bearer token for the invenio repository."""

    host_url: YarlURL
    """URL of the repository."""

    token: str
    """Bearer token for the repository."""

    def __post_init__(self):
        """Cast the host_url to YarlURL if it is not already."""
        if not isinstance(self.host_url, URL):
            self.host_url = URL(self.host_url)
        assert self.token is not None, "Token must be provided"
