"""Functions for MCNP model text printing."""

from __future__ import annotations

from typing import Any

from logging import getLogger

from mckit import constants
from mckit.utils import get_decades, prettify_float, significant_digits

IMPORTANCE_FORMAT = "{0:.3f}"

_LOG = getLogger(__name__)


def print_card(tokens: list[str], offset: int = 8, max_column: int = 80, sep: str = "\n") -> str:
    """Produce string in MCNP card format.

    Args:
        tokens :
            List of words to be printed.
        offset :
            The number of spaces to make continuation of line. Minimum 5.
        max_column :
            The maximum length of card line. Maximum 80.
        sep :
            Separator symbol. This symbol marks positions where newline character
            should be inserted even if max_column position not reached.

    Returns:
        MCNP code of a card.
    """
    if offset < 5:
        offset = 5
        _LOG.warning("offset must not be less than 5. offset is set to be 5.")
    if max_column > 80:
        max_column = 80
        _LOG.warning("max_column must not be greater than 80. It is set to be 80.")

    length = 0  # current length.
    words = []  # a list of individual words.
    line_sep = "\n" + " " * offset  # separator between lines.
    i = 0
    while i < len(tokens):
        if length + len(tokens[i]) > max_column or tokens[i] == sep:
            words.append(line_sep)
            length = offset
            while tokens[i] == sep or tokens[i].isspace():
                i += 1
                if i == len(tokens):
                    words.pop()
                    return "".join(words)
        words.append(tokens[i])
        length += len(tokens[i])
        i += 1
    return "".join(words)


def separate(tokens: list[str], sep: str = " ") -> list[str]:
    """Adds separation symbols between tokens.

    Args:
        tokens :
            A list of strings.
        sep :
            Separator to be inserted between tokens. Default: single space.

    Returns:
        List of separated tokens.
    """
    sep_tokens = []
    for t in tokens[:-1]:
        sep_tokens.append(t)
        sep_tokens.append(sep)
    sep_tokens.append(tokens[-1])
    return sep_tokens


def print_option(option: str, value: Any) -> list[str]:
    name = option[:3]
    par = option[3:]
    if name == "IMP" and (par in ("N", "P", "E")):
        return [f"IMP:{par}={IMPORTANCE_FORMAT.format(value)}"]
    if option == "VOL":
        return [f"VOL={value}"]
    if option == "U":
        return [f"U={value.name()}"]
    if option == "FILL":
        universe = value["universe"]
        tr = value.get("transform", None)
        words = [f"FILL={universe.name()}"]
        if tr:
            tr_name = tr.name()
            if not tr_name:
                words[0] = "*" + words[0]
                words.append("(")
                words.extend(tr.get_words())
                words.append(")")
            else:
                words.append("(")
                words.append(str(tr_name))
                words.append(")")
        return words
    raise ValueError(f"Incorrect option name: {option}")


def pretty_float(value: float, frac_digits: int | None = None) -> str:
    """Pretty print of the float number.

    Args:
        value :
            Value to be printed.
        frac_digits :
            The number of digits after decimal point.
    """
    if value == -0.0:
        value = 0.0

    if frac_digits is None:
        frac_digits = significant_digits(
            value, constants.FLOAT_TOLERANCE, resolution=constants.FLOAT_TOLERANCE
        )
    decades = get_decades(value)
    format_f = f"{{0:.{max(frac_digits, 0)}f}}"
    format_e = f"{{0:.{max(frac_digits + decades, 0)}e}}"
    text_f = format_f.format(round(value, frac_digits))
    text_e = format_e.format(value)
    if len(text_f) <= len(text_e):
        return text_f
    return text_e


CELL_OPTION_GROUPS = (
    ("IMPN", "IMPP", "IMPE", "VOL"),  # Importance options
    ("TRCL",),  # Transformation options
    ("U", "FILL"),  # Universe and fill options
)


def add_float(words: list[str], v: float, pretty: bool) -> None:
    words.append(" ")
    if pretty:
        words.append(pretty_float(v))
    else:
        words.append(prettify_float(v))
