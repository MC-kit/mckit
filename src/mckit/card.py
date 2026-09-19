"""Features, common for all cards."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from abc import ABC, abstractmethod
from collections.abc import Callable

from mckit.utils.named import Name

from .printer import print_card
from .utils import match_comment

if TYPE_CHECKING:
    from typing import Any

    import re


# noinspection PyPropertyDefinition
class Card(ABC):
    """Features, common for all cards."""

    def __init__(self, **options: Any) -> None:
        # TODO @dvp: rename self.options to self._options to make this attribute private
        #            make sure that other modules don't access options directly
        #            at least for name, comment and so on
        #            then convert options to separate explicit attributes
        self.options: dict[str, Any] = options

    @override
    def __str__(self):
        # TODO dvp: option `name` is printed twice,
        #           (second time as option)
        #           This should be explicit property of this class instance
        return f'{self.name()}: "{self.options}"'

    @property
    def is_anonymous(self) -> bool:
        """Check if the card has name."""
        return self.name() is None

    @property
    def has_original(self) -> bool:
        """Has original text stored in options."""
        return "original" in self.options

    @property
    def original(self) -> str | None:
        """Original text from an MCNP model."""
        return self.options.get("original")

    @property
    def has_comment_above(self) -> bool:
        """Has comment above stored in options."""
        return "comment_above" in self.options

    @property
    def comment_above(self) -> str | None:
        """Comment located above this card in an MCNP model."""
        return self.options.get("comment_above")

    def name(
        self,
    ) -> (
        Name | None
    ):  # TODO dvp: we'd better have special property name, don't use options for that
        """Returns card's name."""
        return self.options.get("name", None)

    def rename(self, new_name: Name) -> Card:
        """Renames the card."""
        self.options["name"] = new_name
        self.drop_original()
        return self

    @abstractmethod
    def mcnp_words(self, pretty=False) -> list[str]:
        """Gets a list of card words."""

    def mcnp_repr(self, pretty: bool = False) -> str:
        """Get string representation of the card.

        Parameters
        ----------
        pretty
            print float number in human-readable format
        """
        # TODO @dvp: try to use original texts, if available - this will preserve comments
        # TODO @dvp: remove `pretty`, instead use formats for numbers from geouned, to avoid precision loss
        return print_card(self.mcnp_words(pretty))

    def drop_original(self) -> None:
        """Drop original text, if any.

        Do this, if the card is changed and doesn't correspond to original text anymore.
        """
        if "original" in self.options:
            del self.options["original"]

    def add_comment(self, *comment: str) -> None:
        """Add a comment to this card."""
        self.options.setdefault("comment", []).extend(comment)

    @override
    def __hash__(self) -> int:
        _n = self.name()
        return _n if _n is not None else 0

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Card) and (self is other or self.options == other.options)

    def match_comment(self, predicate: str | re.Pattern | Callable[[str], bool]) -> bool:
        """Check if this cell trailing comment matches `predicate`.

        Parameters
        ----------
        predicate
            what to search for in the comments (string, pattern or callable)

        Returns
        -------
        Does predicate match one of the  comment lines?
        """
        comment = self.options.get("comment")
        if comment is None:
            return False
        return match_comment(comment, predicate)


__all__ = ["Card"]
