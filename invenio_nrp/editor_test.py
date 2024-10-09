#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
from typing_extensions import Union


class A:
    a = 1
    aa = 2


class B:
    b = 1
    bb = 3


def f() -> Union[A, B]:
    pass
