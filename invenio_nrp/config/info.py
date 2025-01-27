#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Repository info endpoint response types."""

from typing import Optional

from attrs import define, field
from yarl import URL

from ..converter import Rename, extend_serialization
from ..types import Model


@extend_serialization(Rename("self", "self_"), allow_extra_data=True)
@define(kw_only=True)
class RepositoryInfoLinks(Model):
    """Links within the repository info endpoint."""

    self_: URL
    """Link to the repository itself"""

    records: URL
    """Link to the global search endpoint"""

    user_records: URL
    """Link to the user's records"""

    models: Optional[URL]
    """Link to the models in the repository"""

    requests: URL
    """Link to the requests in the repository"""


@define(kw_only=True)
class ModelInfoLinks:
    """Links within the model info endpoint."""

    api: URL
    """Link to the model records' API listing"""

    html: URL
    """Link to the model records' HTML listing page"""

    model: URL
    """Link to the model definition"""

    published: URL
    """Link to the published records"""

    user_records: Optional[URL]
    """Link to the user's draft records"""

    schemas: dict[str, URL] = field(factory=dict)
    """Link to the model expanded jsonschema and other schemas"""


@define(kw_only=True)
class ModelInfoAccept:
    """Acceptable content-types for the model."""

    accept: str
    """The content-type accepted by the model"""

    name: str | None = None
    """The name of the content-type"""

    description: str | None = None
    """The description of the content-type"""


@define(kw_only=True)
class ModelInfo:
    """Information about metadata model within invenio server."""

    name: str
    """The name of the model"""

    description: str
    """The description of the model"""

    version: str
    """The version of the model"""

    features: list[str]
    """List of features supported by the model"""

    links: ModelInfoLinks
    """Links to the model"""

    accept: list[ModelInfoAccept] = field(factory=list)
    """List of supported content-types for API serialization"""
    

@define(kw_only=True)
class RepositoryInfo:
    """Extra info downloaded from nrp-compatible invenio repository."""

    name: str
    """The name of the repository"""

    description: str
    """The description of the repository"""

    version: str
    """The version of the repository"""

    invenio_version: str
    """The version of invenio the repository is based on"""

    links: RepositoryInfoLinks
    """Links to the repository"""

    transfers: list[str] = field(factory=list)
    """List of supported file transfer protocols"""

    models: dict[str, ModelInfo] = field(factory=dict)
