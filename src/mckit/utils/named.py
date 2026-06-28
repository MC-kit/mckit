"""Name of objects, specific integers."""

from __future__ import annotations

from typing import NewType, Protocol, cast

from collections.abc import Iterable

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


def check_name_is_int(name: int | None) -> int:
    """Check if a card  name is an integer."""
    if name is None:
        raise ValueError("name cannot be None")
    return name


def map_names(cards: Iterable[HasName]) -> Iterable[int]:
    """Iterate over card names(numbers)."""
    return (check_name_is_int(c.name()) for c in cards)
