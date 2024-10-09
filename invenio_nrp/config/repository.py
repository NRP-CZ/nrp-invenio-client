#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel
from yarl import URL

from invenio_nrp.types import RepositoryInfo
from invenio_nrp.types.yarl_url import YarlURL

"""
Configuration of the repository and repository access classes.
"""

WrappedFnReturnT = TypeVar("WrappedFnReturnT")
WrappedFn = TypeVar("WrappedFn", bound=Callable[..., Any])


class RepositoryConfig(BaseModel):
    alias: str
    """The local alias of the repository."""

    url: YarlURL
    """The api URL of the repository, usually something like https://repository.org/api."""

    token: Optional[str] = None
    """Bearer token"""

    verify_tls: bool = False
    """Verify the TLS certificate in https"""

    retry_count: int = 10
    """Number of times idempotent operations will be retried if something goes wrong."""

    retry_after_seconds: int = 10
    """If server does not suggest anything else, retry after this interval in seconds"""

    info: Optional[RepositoryInfo] = None
    """Cached repository info"""

    class Config:
        extra = "forbid"

    @property
    def well_known_repository_url(self) -> YarlURL:
        return self.url / ".well-known" / "repository/"

    def search_url(self, model: str | None) -> YarlURL:
        model = model or self._default_model_name
        if model:
            return self.info.models[model].links.published
        return self.info.links.records

    def user_search_url(self, model: str | None) -> YarlURL:
        model = model or self._default_model_name
        if model:
            return self.info.models[model].links.user_records
        return self.info.links.user_records

    def create_url(self, model: str | None) -> YarlURL:
        model = model or self._default_model_name
        if model:
            return self.info.models[model].links.api
        return self.info.links.records

    def read_url(self, model: str | None, record_id: str) -> YarlURL:
        if record_id.startswith("https://"):
            return URL(record_id)
        model = model or self._default_model_name
        if model:
            return self.info.models[model].links.api / record_id
        return self.info.links.records / record_id

    def user_read_url(self, model: str | None, record_id: str) -> YarlURL:
        if record_id.startswith("https://"):
            return URL(record_id)
        model = model or self._default_model_name
        if model:
            return self.info.models[model].links.api / record_id / "draft"
        return self.info.links.records / record_id / "draft"

    @property
    def requests_url(self) -> YarlURL:
        return self.info.links.requests

    @property
    def _default_model_name(self) -> str | None:
        if self.info and len(self.info.models) == 1:
            return next(iter(self.info.models))
        return None
