#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import dataclasses
from datetime import datetime

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from yarl import URL

from .yarl_url import YarlURL


class Model(BaseModel):
    class Config:
        extra = "allow"

    def __getattr__(self, item):
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


@dataclasses.dataclass
class URLBearerToken:
    host_url: YarlURL
    token: str

    def __post_init__(self):
        if not isinstance(self.host_url, URL):
            self.host_url = YarlURL(self.host_url)
        assert self.token is not None, "Token must be provided"
