#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import dataclasses
from types import SimpleNamespace
from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel
from typing_extensions import get_args


@dataclasses.dataclass
class GenericsArguments:
    _cache: Dict[Type, SimpleNamespace] = dataclasses.field(default_factory=dict)
    _type_names_cache: Dict[Type, List[str]] = dataclasses.field(default_factory=dict)

    def actual_types(self, obj: Any, **default_types) -> SimpleNamespace:
        key = (type(obj), frozenset(default_types.items()))

        if key in self._cache:
            return self._cache[type(obj)]

        generic_type_names = self._extract_generic_type_names(type(obj))

        orig_class = getattr(obj, "__orig_class__", None)
        if orig_class:
            # if there is an orig class, the object was instantiated as Blah[int](), so extract the actual types from the orig class
            actual_types = self._extract_actual_types_from_orig_class(orig_class)
        elif isinstance(obj, BaseModel):
            # if the object has pydantic metadata, extract the actual types from there
            actual_types = self._extract_actual_types_from_pydantic(type(obj))
        else:
            # otherwise the object was subclassed from Blah[int], so extract the actual types from the MRO
            actual_types = self._extract_actual_types_from_mro(type(obj))
            if actual_types is None:
                actual_types = [None] * len(generic_type_names)

        assert len(generic_type_names) == len(
            actual_types
        ), f"Generic type names {generic_type_names} and actual types {actual_types} do not match"

        resolved_types = {}
        for k, v in zip(generic_type_names, actual_types):
            if isinstance(v, TypeVar):
                v = v.__bound__
                if not v:
                    if k not in default_types:
                        raise ValueError(
                            f"No default type provided for {k} and no bound was present on the TypeVar"
                        )
                    v = default_types[k]
            if not v:
                if k not in default_types:
                    raise ValueError(
                        f"No default type provided for {k} and no bound was present on the TypeVar"
                    )
                v = default_types[k]
            resolved_types[k] = v

        ns = SimpleNamespace(**resolved_types)

        self._cache[type(obj)] = ns
        return ns

    def _extract_actual_types_from_orig_class(self, orig_class: Type) -> List[Type]:
        return [arg for arg in get_args(orig_class)]

    def _extract_actual_types_from_pydantic(self, clz: Type):
        for m in clz.mro():
            pydantic_metadata = getattr(m, "__pydantic_generic_metadata__", None)
            if pydantic_metadata and pydantic_metadata["args"]:
                return pydantic_metadata["args"]
        raise ValueError(
            f"Could not extract pydantic metadata from {clz}, no typing args found on class or any ancestors"
        )

    def _extract_actual_types_from_mro(self, clz: Type) -> List[Type] | None:
        for m in clz.mro():
            for base_class in getattr(m, "__orig_bases__", []):
                ret = []
                for arg in get_args(base_class):
                    if isinstance(arg, TypeVar):
                        continue
                    ret.append(arg)
                if ret:
                    return ret
        return None

    def _extract_generic_type_names(self, clz: Type):
        if clz in self._type_names_cache:
            return self._type_names_cache[clz]
        for m in clz.mro():
            generic_names = self._extract_generic_type_names_from_class(m)
            if generic_names:
                self._type_names_cache[clz] = generic_names
                return generic_names
        raise ValueError(f"Could not extract generic type names from {clz}")

    def _extract_generic_type_names_from_class(self, clz: Type) -> List[str]:
        orig_bases = getattr(clz, "__orig_bases__", [])
        for base in orig_bases:
            # nasty hack to filter out just Generic, it should be GenericAlias but that is not exposed
            if not repr(base).startswith("typing.Generic["):
                continue
            ret = []
            for param in get_args(base):
                if isinstance(param, TypeVar):
                    ret.append(param.__name__)
            if ret:
                return ret
        else:
            return []


generic_arguments = GenericsArguments()
