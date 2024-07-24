"""Features, common for all cards."""

from __future__ import annotations

from typing import Any, cast

from abc import ABC, abstractmethod
from functools import reduce
from operator import xor

from mckit.utils.named import Name

from .printer import print_card
from .utils import make_hashable


class Card(ABC):
    """Features, common for all cards."""

    def __init__(self, **options):
        self.options: dict[str, Any] = options

    def __str__(self):
        # TODO dvp: option `name` is printed twice,
        #           (second time as option)
        #           This should be explicit property of this class instance
        return f'{self.name()}: "{self.options}"'

    @property
    def is_anonymous(self) -> bool:
        """Is the card is named?"""
        return self.name() is None

    @property
    def has_original(self) -> bool:
        """Has original text stored in options."""
        return "original" in self.options

    @property
    def original(self) -> str | None:
        """Original text from an MCNP model."""
        return cast(str | None, self.options.get("original", None))

    @property
    def has_comment_above(self) -> bool:
        """Has comment above stored in options."""
        return "comment_above" in self.options

    @property
    def comment_above(self) -> str | None:
        """Comment located above this card in an MCNP model."""
        return cast(str | None, self.options.get("comment_above", None))

    def name(
        self,
    ) -> (
        Name | None
    ):  # TODO dvp: we'd better have special property name, don't use options for that
        """Returns card's name."""
        return self.options.get("name", None)

    def rename(self, new_name) -> Card:
        """Renames the card."""
        self.options["name"] = new_name
        self.drop_original()
        return self

    @abstractmethod
    def mcnp_words(self, pretty=False) -> list[str]:
        """Gets a list of card words."""

    def mcnp_repr(self, pretty: bool = False) -> str:
        """Gets str representation of the card."""
        # TODO dvp: try to use original texts, if available - this will preserve comments
        return cast(str, print_card(self.mcnp_words(pretty)))

    def drop_original(self) -> None:
        """Drop original text, if any.

        Do this, if the card is changed and doesn't correspond to original text anymore.
        """
        if "original" in self.options:
            del self.options["original"]

    def add_comment(self, *comment: str) -> None:
        """Add a comment to this card."""
        self.options.setdefault("comment", []).extend(comment)

    def __hash__(self) -> int:
        return reduce(xor, (hash(k) ^ hash(make_hashable(v)) for k, v in self.options.items()), 0)

    def __eq__(self, other) -> bool:
        return self is other or self.options == other.options
