"""Split MCNP code to cards as text segments separating them by kind."""

from __future__ import annotations

from typing import TextIO

import re
import sys

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import IntEnum

BLANK_LINE_PATTERN = re.compile(r"\n\s*\n", flags=re.MULTILINE)
COMMENT_LINE_PATTERN = re.compile(r"^\s{,5}[cC]( .*)?\s*$")
# pattern to remove comments from a card text
REMOVE_COMMENT_PATTERN = re.compile(
    r"(\s*\$.*$)|(^\s{0,5}c\s.*\n?)", flags=re.MULTILINE | re.IGNORECASE
)
# pattern to split section text to optional "comment" and subsequent MCNP card pairs
# noinspection RegExpUnexpectedAnchor
CARD_PATTERN = re.compile(
    r"(?P<comment>((^\s{,5}c( .*)?\s*$)\n?)+)?"
    r"(?P<card>^\s{,5}(\*|\+|\w).*(\n((^\s{,5}c.*\n?)*^\s{5,}\S.*\n?)*)?)?",
    flags=re.MULTILINE | re.IGNORECASE,
)

# pattern to replace subsequent spaces with a single one
SPACE_PATTERN = re.compile(r"\s+", flags=re.MULTILINE)

SDEF_PATTERN = re.compile(r"(sdef)|(s[ibp]\d+)|(ds\d+)|(wwp.*)", re.IGNORECASE)

# pattern to match labels of cards relevant for tallies section
TALLY_PATTERN = re.compile(r"(?P<tag>f(c|(m(esh)?)?)|(e)|(d[ef]))(?P<number>\d+)", re.IGNORECASE)


class Kind(IntEnum):
    """A card class tag."""

    COMMENT = 0
    CELL = 1
    SURFACE = 2
    MATERIAL = 3
    TRANSFORMATION = 4
    SDEF = 5
    TALLY = 6
    GENERIC = 7

    @classmethod
    def from_card_text(cls, text: str) -> Kind:
        """Create a data or comment card tag based on a card text."""
        label: str = text.split(maxsplit=2)[0]
        label = label.strip()
        if label[0] in "mM" and str.isdigit(label[1]):
            return Kind.MATERIAL
        # check if a label is for transformation card, example: TR20 or *tr1
        i = 0
        if label[0] == "*":
            i = 1
        if label[i] in "tT" and label[i + 1] in "rR" and str.isdigit(label[i + 2]):
            return Kind.TRANSFORMATION
        if SDEF_PATTERN.match(label):
            return Kind.SDEF
        if TALLY_PATTERN.match(label):
            return Kind.TALLY
        if is_comment(text):
            return Kind.COMMENT
        return Kind.GENERIC


@dataclass
class Card:
    """Generic MCNP card raw text item.

    The card kind is defined either from parsing context (for cells and surfaces) or
    from card label
    """

    text: str
    kind: Kind | None = field(default=None)

    # noinspection PyUnusedLocal,PyUnresolvedReferences
    def __post_init__(self) -> None:
        if self.kind is None:
            self.kind = Kind.from_card_text(self.text)

    @property
    def is_comment(self) -> bool:
        return self.kind is Kind.COMMENT

    @property
    def is_material(self) -> bool:
        return self.kind is Kind.MATERIAL

    @property
    def is_transformation(self) -> bool:
        return self.kind is Kind.TRANSFORMATION

    @property
    def is_cell(self) -> bool:
        return self.kind is Kind.CELL

    @property
    def is_surface(self) -> bool:
        return self.kind is Kind.SURFACE

    @property
    def is_sdef(self) -> bool:
        return self.kind is Kind.SDEF

    @property
    def is_tally(self) -> bool:
        return self.kind is Kind.TALLY

    def get_clean_text(self) -> str:
        return get_clean_text(self.text)

    def __str__(self) -> str:
        return self.text

    @property
    def name(self) -> str:
        assert not self.is_comment, "Comment cannot have name"
        return self.text.split(maxsplit=2)[0]

    @property
    def number(self) -> int:
        name = self.name
        if self.is_cell:
            return int(name)
        if self.is_surface:
            if name.isdigit():
                return int(name)
            assert name[0] in "%*", "Expected reflecting, white surface"
            return int(name[1:])
        if self.is_material:
            return int(name[1:])
        if self.is_transformation:
            i = 0
            if name[0] == "*":
                i = 1
            if name[i] in "tT" and name[i + 1] in "rR" and name[i + 2 :].isdigit():
                return int(name[i + 2 :])
        raise NotImplementedError(f"Cannot define number for {self.kind} card {name!r}")


@dataclass
class InputSections:
    title: str | None = field(default=None)
    cell_cards: list[Card] | None = field(default=None)
    surface_cards: list[Card] | None = field(default=None)
    data_cards: list[Card] | None = field(default=None)
    message: str | None = field(default=None)
    remainder: str | None = field(default=None)
    is_continue: bool = field(default=False)

    def __post_init__(self) -> None:
        if self.is_continue:
            if self.cell_cards or self.surface_cards:
                raise ValueError("Cells and Surfaces shouldn't present in 'continue' mode model")
            if not self.data_cards:
                raise ValueError("At least one data card should present in 'continue' mode model")

    def print(self, stream: TextIO = sys.stdout) -> None:
        if self.message:
            print(self.message, file=stream)
            print(file=stream)
        if self.title:
            print(self.title, file=stream)
        if not self.is_continue:
            if self.cell_cards is None:
                msg = "No cell cards"
                raise ValueError(msg)
            for card in self.cell_cards:
                print(card.text, file=stream)
            print(file=stream)
            if self.surface_cards is None:
                msg = "No surface cards"
                raise ValueError(msg)
            for card in self.surface_cards:
                print(card.text, file=stream)
            print(file=stream)
        if self.data_cards:
            for card in self.data_cards:
                print(card.text, file=stream)
            print(file=stream)
        if self.remainder:
            print(self.remainder, file=stream)


def split_to_cards(text: str, kind: Kind | None = None) -> Iterator[Card]:
    for res in CARD_PATTERN.finditer(text):
        groups = res.groupdict()
        comment = groups["comment"]
        card = groups["card"]
        if comment:
            comment = comment.rstrip()
            yield Card(comment, kind=Kind.COMMENT)
        if card:
            card = card.rstrip()
            _kind = Kind.from_card_text(card) if kind is None else kind
            yield Card(card, kind=_kind)


def parse_sections(inp: TextIO) -> InputSections:
    return parse_sections_text(inp.read())


# noinspection PyIncorrectDocstring,PyUnresolvedReferences
def parse_sections_text(text: str) -> InputSections:
    """Splits input file to sections according to mcnp input format.

    The parser provides minimal separation of text sections from the input file
    based on Blank Line Delimiter entries
    The sections can be parsed later and in order different from the input file
    using specific low level parsers for cell, surface and data cards.

    Notes:
        From MCNP manual:

        An input file has the following form::
            Message Block           | Optional
            Blank Line Delimiter    | Required if Message Block is present
            Title Card
            Cell Cards
            Blank Line Delimiter
            Surface Cards
            Blank Line Delimiter
            Data Cards
            Blank Line Terminator    | Recommended
            Anything Else            | Optional

    Args:
        text: MCNP text

    Raises:
        ValueError: if the input is inconsistent.

    Returns:
        mcnp_input_sections object, containing text of sections from the file
    """

    message = None
    cell_cards = None
    surface_cards = None
    data_cards = None
    remainder = None

    sections = BLANK_LINE_PATTERN.split(text, 5)

    # The first line can be a message or a title.
    kw = sections[0][: len("message:")].lower()

    i = 0

    if kw == "message:":
        message = sections[0]
        i += 1

    title, cur_section = sections[i].split("\n", 1)
    i += 1
    if not title:
        raise ValueError("Cannot find the MCNP model title")

    is_continue = check_title_is_continue(title)

    if is_continue:
        data_cards = list(split_to_cards(cur_section))
        if i < len(sections):
            remainder = "\n\n".join(sections[i:])
        result = InputSections(
            title,
            cell_cards=cell_cards,
            surface_cards=surface_cards,
            data_cards=data_cards,
            message=message,
            remainder=remainder,
            is_continue=True,
        )
    else:
        cell_cards = list(split_to_cards(cur_section, kind=Kind.CELL))
        if i < len(sections):
            cur_section = sections[i]
            surface_cards = list(split_to_cards(cur_section, kind=Kind.SURFACE))
            i += 1
            if i < len(sections):
                cur_section = sections[i]
                data_cards = list(split_to_cards(cur_section, kind=None))
                i += 1
                if i < len(sections):
                    remainder = "\n\n".join(sections[i:])
        result = InputSections(
            title,
            cell_cards=cell_cards,
            surface_cards=surface_cards,
            data_cards=data_cards,
            message=message,
            remainder=remainder,
            is_continue=False,
        )

    return result


CONTINUE_LEN = len("continue")


def check_title_is_continue(title: str) -> bool:
    return title[:CONTINUE_LEN].lower() == "continue"


def is_comment(text: str) -> bool:
    if "\n" in text:
        res = next((line for line in text.split("\n") if not is_comment_line(line)), False)
        return not res
    return is_comment_line(text, skip_asserts=True)


def is_comment_line(line: str, skip_asserts=False) -> bool:
    if not skip_asserts:
        assert isinstance(line, str), "The parameter 'line' should be text"
        assert "\n" not in line, "The parameter 'line' should be the single text line"
    return COMMENT_LINE_PATTERN.match(line) is not None


def get_clean_text(text: str) -> str:
    without_comments = REMOVE_COMMENT_PATTERN.sub("", text)
    return SPACE_PATTERN.sub(" ", without_comments)


def clean_mcnp_cards(iterable: Iterable[Card]) -> Iterator[Card]:
    for x in iterable:
        if x.kind is not Kind.COMMENT:
            clean_text = x.get_clean_text()
            t = Card(clean_text, kind=x.kind)
            yield t


def distribute_cards(
    cards: Iterable[Card],
) -> tuple[list[Card], list[Card], list[Card], list[Card], list[Card]]:
    comment: Card | None = None

    def append(_cards: list[Card], _card: Card) -> None:
        nonlocal comment
        if comment:
            _cards.append(comment)
            comment = None
        _cards.append(_card)

    # fmt: off
    materials, transformations, sdef, tallies, others = \
        [], [], [], [], []  # type: list[Card], list[Card], list[Card], list[Card], list[Card]
    # fmt: on

    for card in cards:
        if card.is_comment:
            assert comment is None
            comment = card
        elif card.is_material:
            append(materials, card)
        elif card.is_transformation:
            append(transformations, card)
        elif card.is_sdef:
            append(sdef, card)
        elif card.is_tally:
            append(tallies, card)
        else:
            append(others, card)

    if comment:
        others.append(comment)

    return materials, transformations, sdef, tallies, others
