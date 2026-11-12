from __future__ import annotations

import re

import mckit.parser.common.utils as cmn

from mckit.parser.common.utils import drop_c_comments, extract_comments
from mckit.transformation import Transformation


def parse(text: str) -> Transformation:
    """Parse MCNP transformation specification.

    Parameters
    ----------
    text : str
        Transformation specification.

    Returns
    -------
    Transformation: representation of an MCNP transformation.

    Raises
    ------
    ValueError: on invalid transformation definition.
    """
    text = drop_c_comments(text)
    text, _comments, trailing_comments = extract_comments(text)
    result = _parse_transformation(text)
    if trailing_comments:
        result.comment = trailing_comments
    return result


def _parse_transformation(text: str) -> Transformation:
    header_match = _TRANSFORMATION_CARD_PATTERN.match(text)
    if header_match is None:
        raise cmn.ParseError(
            f"Transformation specification must start with 'tr<number>', got: '{text.strip()}'"
        )
    name = int(header_match.group("name"))
    indegrees = header_match.group("star") is not None
    translation, rotation, inverted = _collect_params(_collect_numbers(text, header_match.end()))
    return Transformation(
        translation=translation,
        rotation=rotation,
        indegrees=indegrees,
        inverted=inverted,
        name=name,
    )


_TRANSFORMATION_CARD_PATTERN = re.compile(
    r"""^\s{0,5}(?P<star>\*)?tr(?P<name>\d+)   # transformation label, like *tr2
    """,
    re.IGNORECASE | re.VERBOSE,
)

_NUMBER_PATTERN = re.compile(cmn.FLOAT, re.IGNORECASE)

_PURE_INTEGER_PATTERN = re.compile(r"[-+]?\d+$")


def _collect_numbers(text: str, pos: int) -> list[tuple[float, bool]]:
    """Find numbers in the rest of the card.

    Returns
    -------
        List of pairs: value and flag, whether the number is written as a plain integer.
    """
    matches = _NUMBER_PATTERN.finditer(text, pos=pos)
    return [
        (float(match.group()), _PURE_INTEGER_PATTERN.match(match.group()) is not None)
        for match in matches
    ]


_ROTATION_LENGTHS = frozenset({3, 5, 6, 9})


def _collect_params(
    numbers: list[tuple[float, bool]],
) -> tuple[list[float], list[float] | None, bool]:
    """Extract translation and rotation vectors from found numbers.

    The first 3 numbers are translation, the rest are rotation,
    optionally followed with an integer M option (only -1 or 1).
    """
    if len(numbers) < 3:
        raise cmn.ParseError(
            "Transformation specification requires a translation vector of 3 numbers"
        )
    translation = [value for value, _is_int in numbers[:3]]
    tail = numbers[3:]
    if not tail:
        return translation, None, False
    if len(tail) not in _ROTATION_LENGTHS | {10}:
        raise cmn.ParseError(f"Invalid number of transformation rotation parameters: {len(tail)}")
    if len(tail) == 10:  # 9 rotation numbers followed with the M option
        value, is_int = tail[-1]
        if not is_int:
            raise cmn.ParseError("The M option should be specified as an integer")
        if value not in {-1.0, 1.0}:
            raise ValueError(f"Invalid M option value {int(value)}")
        return translation, [value for value, _is_int in tail[:-1]], value == -1.0
    return translation, [value for value, _is_int in tail], False
