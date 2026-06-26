"""Name of objects, specific integers."""

from __future__ import annotations

from typing import NewType, Protocol, cast

Name = NewType("Name", int)
"""The card names are integer."""


class HasName(Protocol):
    """Something with name() method."""

    def name(self) -> int | Name: ...


def default_name_key(x: HasName) -> Name:
    """Get a card name.

    Used for mapping cards collection to int collections.

    Parameters
    ----------
    x
        card with name
    """
    return cast(Name, x.name())
