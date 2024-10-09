#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .yarl_url import YarlURL


class RepositoryInfoLinks(BaseModel):
    self_: Optional[YarlURL] = Field(alias="self", default=None)
    """Link to the repository itself"""

    records: YarlURL
    """Link to the global search endpoint"""

    user_records: YarlURL
    """Link to the user's records"""

    models: Optional[YarlURL] = None
    """Link to the models in the repository"""

    requests: YarlURL
    """Link to the requests in the repository"""

    class Config:
        extra = "forbid"


class ModelInfoLinks(BaseModel):

    api: YarlURL
    """Link to the model records' API listing"""

    html: YarlURL
    """Link to the model records' HTML listing page"""

    schemas: Dict[str, YarlURL] = Field(alias="schemas")
    """Link to the model expanded jsonschema and other schemas"""

    model: YarlURL
    """Link to the model definition"""

    published: YarlURL
    """Link to the published records"""

    user_records: Optional[YarlURL] = Field(alias="user_records", default=None)
    """Link to the user's draft records"""

    class Config:
        extra = "forbid"


class ModelInfo(BaseModel):

    name: str
    """The name of the model"""

    description: str
    """The description of the model"""

    version: str
    """The version of the model"""

    features: List[str]
    """List of features supported by the model"""

    schemas: Dict[str, str]
    """List of schema identifiers by content-type supported by the model"""

    links: ModelInfoLinks
    """Links to the model"""

    class Config:
        extra = "forbid"


class RepositoryInfo(BaseModel):
    """Extra info downloaded from nrp-compatible invenio repository"""

    name: str
    """The name of the repository"""

    description: str
    """The description of the repository"""

    version: str
    """The version of the repository"""

    invenio_version: str
    """The version of invenio the repository is based on"""

    transfers: List[str]
    """List of supported file transfer protocols"""

    links: RepositoryInfoLinks
    """Links to the repository"""

    models: Dict[str, ModelInfo] = Field(default_factory=dict)

    class Config:
        extra = "forbid"
