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


_CARD_OPTION_KEYS = ("original", "comment", "comment_above")
"""Keys of the card-level attributes, which used to be stored in the options dictionary."""

CARD_SLOTS = ("_name", "_original", "_comment", "_comment_above", "_extra")
"""Slots for the card-level attributes, to be declared by the derived classes.

`Card` itself must stay dict-based (see the class docstring),
so the derived classes shadow the card-level attributes with their own slots.
"""


# noinspection PyPropertyDefinition
class Card(ABC):
    """Features, common for all cards.

    NOTE: `Card` must not declare `__slots__` with data entries.
    The compiled geometry C-types (see mckit.geometry) are solid,
    so any Python base of the `Surface` class hierarchy with a non-empty
    `__slots__` breaks the multiple inheritance with those C-types
    ("multiple bases have instance lay-out conflict").
    Instead, the derived classes shadow the card-level attributes
    with their own `__slots__` entries (see CARD_SLOTS), which keeps
    instances of those classes dict-free.
    """

    def __init__(
        self,
        name: Name | int | None = None,
        *,
        original: str | None = None,
        comment: list[str] | None = None,
        comment_above: str | None = None,
        **extra: Any,
    ) -> None:
        self._name: Name | int | None = name
        self._original: str | None = original
        self._comment: list[str] | None = comment
        self._comment_above: str | None = comment_above
        self._extra: dict[str, Any] | None = extra or None

    @staticmethod
    def _split_options(options: dict[str, Any]) -> dict[str, Any]:
        """Extract the card-level attributes from a transitional options dictionary.

        The popped keys are to be forwarded to `Card.__init__` as keyword arguments,
        the rest of the options stay with the derived class.
        """
        return {key: options.pop(key) for key in _CARD_OPTION_KEYS if key in options}

    def _card_options(self, *, drop_original: bool = False) -> dict[str, Any]:
        """Transitional: the card-level attributes in the legacy options dictionary form.

        Used to propagate the card-level attributes to derived objects
        the way the whole options dictionary was propagated before.
        """
        result: dict[str, Any] = {}
        if not drop_original and self._original is not None:
            result["original"] = self._original
        if self._comment is not None:
            result["comment"] = self._comment
        if self._comment_above is not None:
            result["comment_above"] = self._comment_above
        return result

    def _options_state(self) -> dict[str, Any]:
        """Transitional: the options, which are not card-level attributes yet, for equality."""
        return {}

    @override
    def __str__(self):
        return f'{self.name()}: "{self._extra or {}}"'

    @property
    def is_anonymous(self) -> bool:
        """Check if the card has name."""
        return self.name() is None

    @property
    def has_original(self) -> bool:
        """Check if the original text is stored."""
        return self._original is not None

    @property
    def original(self) -> str | None:
        """Original text from an MCNP model."""
        return self._original

    @original.setter
    def original(self, value: str | None) -> None:
        self._original = value

    @property
    def has_comment_above(self) -> bool:
        """Check if the comment above is stored."""
        return self._comment_above is not None

    @property
    def comment_above(self) -> str | None:
        """Comment located above this card in an MCNP model."""
        return self._comment_above

    @comment_above.setter
    def comment_above(self, value: str | None) -> None:
        self._comment_above = value

    @property
    def comment(self) -> list[str] | None:
        """Comment lines, which trail this card."""
        return self._comment

    @comment.setter
    def comment(self, value: list[str] | None) -> None:
        self._comment = value

    def name(
        self,
    ) -> Name | int | None:
        """Returns card's name."""
        return self._name

    def rename(self, new_name: Name) -> Card:
        """Renames the card."""
        self._name = new_name
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
        self._original = None

    def add_comment(self, *comment: str) -> None:
        """Add a comment to this card."""
        if self._comment is None:
            self._comment = []
        self._comment.extend(comment)

    @override
    def __hash__(self) -> int:
        _n = self.name()
        return _n if _n is not None else 0

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Card) and (
            self is other
            or (
                self._name == other._name
                and self._original == other._original
                and self._comment == other._comment
                and self._comment_above == other._comment_above
                and self._extra == other._extra
                and self._options_state() == other._options_state()
            )
        )

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
        comment = self._comment
        if comment is None:
            return False
        return match_comment(comment, predicate)


__all__ = ["CARD_SLOTS", "Card"]
