#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base types for REST communication."""

from .base import Model
from .info import ModelInfo, ModelInfoLinks, RepositoryInfo, RepositoryInfoLinks

__all__ = (
    "RepositoryInfo",
    "RepositoryInfoLinks",
    "ModelInfo",
    "ModelInfoLinks",
    "Model",
)
