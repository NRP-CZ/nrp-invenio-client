#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Base types for invenio REST responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated


class Model(BaseModel):
    """Base pydantic model, which allows getting extra fields via normal dot operator."""

    class Config:  # noqa
        extra = "allow"

    def __getattr__(self, item: str) -> Any:  # noqa: ANN401
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
