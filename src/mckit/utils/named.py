from __future__ import annotations

from typing import NewType, cast

Name = NewType("Name", int)
"""The card names are integer."""


def default_name_key(x) -> Name:
    return cast(Name, x.name())
