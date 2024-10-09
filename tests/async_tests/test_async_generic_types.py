#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from datetime import datetime
from typing import Any, Type

from typing_extensions import get_args

from invenio_nrp.client.async_client.files import File
from invenio_nrp.client.async_client.records import RecordLinks
from invenio_nrp.generic import generic_arguments
from invenio_nrp.types import YarlURL


class A[T]:
    a: T = 0


class B[T](A[T]):
    b: T = 0


class C[X]:
    a: A[X]
    b: B[X]


class D(C[int]):
    pass


def describe_class(name: str, base: Type, indent="  "):
    print(f"{indent}{name}: {base}")
    indent += "  "
    if not base:
        return

    for arg in get_args(base):
        print(f"{indent}Arg: {type(arg)} {arg}")

    if hasattr(base, "__orig_bases__"):
        for b in base.__orig_bases__:
            describe_class("__orig_bases__", b, indent)

    for mro in base.mro()[1:]:
        describe_class(f"MRO of {name}", mro, indent)


def describe(c: Any):
    print(f"Instance:   {c}")
    print(f"Class:      {type(c)}")
    orig_class = getattr(c, "__orig_class__", None)
    describe_class("Orig class", orig_class)
    describe_class("Self class", type(c))


def test_generic_types():
    assert generic_arguments._extract_generic_type_names(A[int]) == ["T"]
    assert generic_arguments._extract_generic_type_names(B[int]) == ["T"]
    assert generic_arguments._extract_generic_type_names(C[int]) == ["X"]
    assert generic_arguments._extract_generic_type_names(D) == ["X"]

    assert generic_arguments.actual_types(A[int]()).T == int
    assert generic_arguments.actual_types(B[int]()).T == int
    assert generic_arguments.actual_types(C[int]()).X == int
    assert generic_arguments.actual_types(D()).X == int


def test_generic_types_async():
    from invenio_nrp.client.async_client.records import Record
    from invenio_nrp.client.async_client.request_types import RequestType
    from invenio_nrp.client.async_client.requests import Request

    class DefaultRequestClass(Request):
        pass

    class DefaultRequestTypeClass(RequestType[Request]):
        pass

    class DefaultRecordClass(
        Record[File, DefaultRequestClass, DefaultRequestTypeClass]
    ):
        pass

    drc = DefaultRecordClass(
        links=RecordLinks(
            self=YarlURL("http://example.com"),
            self_html=YarlURL("http://example.com"),
        ),
        metadata=None,
        id="aaa",
        created=datetime.now(),
        updated=datetime.now(),
        revision_id="2",
        files={
            "enabled": False,
        },
    )

    print(drc._generic_arguments)

    drc = Record[File, DefaultRequestClass, DefaultRequestTypeClass](
        links=RecordLinks(
            self=YarlURL("http://example.com"),
            self_html=YarlURL("http://example.com"),
        ),
        metadata=None,
        id="aaa",
        created=datetime.now(),
        updated=datetime.now(),
        revision_id="2",
        files={
            "enabled": False,
        },
    )

    print(drc._generic_arguments)
