from __future__ import annotations

from typing import Any

import re

import mckit.parser.common.utils as cmn  # common parse utils

from mckit.parser.common import TransformationStrictIndex
from mckit.parser.common.utils import drop_c_comments, extract_comments
from mckit.surface import Surface, create_surface
from mckit.utils.indexes import Index


def parse(text: str, transformations: Index | None = None) -> Surface:
    """Parse MCNP surface specification.

    Parameters
    ----------
    text : str
        Surface specification.

    transformations : Index
        Should be one of TransformationStrictIndex, TransformationDummyIndex, IgnoringIndex.
        When None, a TransformationStrictIndex is used.

    Returns
    -------
    Surface: representation of an MCNP surface.

    Raises
    ------
    ValueError: on invalid surface specification.
    """
    if transformations is None:
        transformations = TransformationStrictIndex()
    else:
        assert isinstance(transformations, Index)
    text = drop_c_comments(text)
    text, _comments, trailing_comments = extract_comments(text)
    result = _parse_surface(text, transformations)
    if trailing_comments:
        result.comment = trailing_comments
    return result


def _parse_surface(text: str, transformations: Index) -> Surface:
    header_match = _SURFACE_CARD_PATTERN.match(text)
    if header_match is None:
        raise cmn.ParseError(
            "Surface specification must start with '<modifier?> <name> <transform ambit?> <type>' got: "
            f"'{text.strip()}'"
        )
    kind = _extract_type(header_match)
    options: dict[str, Any] = {
        "name": int(header_match.group("name")),
    }
    if transform := header_match.group("transform"):
        transformation = transformations[int(transform)]
        if transformation:
            options["transform"] = transformation
    if modifier := header_match.group("modifier"):
        options["modifier"] = modifier.strip()
    params = _extract_params(text, header_match.end())
    return create_surface(kind, *params, **options)


_SURFACE_CARD_PATTERN = re.compile(
    r"""^(?:[ \t]{0,5}(?P<modifier>[*+]))?   # optional modifier, should start in first 5 columns
         \s*(?P<name>\d+)\s+                # surface name
         (?:\s*(?P<transform>\d+)\s+)?      # optionally followed by a transformation number
         \s*(?P<stype>[a-z]+(?:/[a-z]+)?)   # surface type, like PX or C/X
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _extract_type(header_match: re.Match) -> str:
    return intern_surface_type(header_match.group("stype"))


_FLOAT_PATTERN = re.compile(cmn.FLOAT, re.IGNORECASE)


def _extract_params(text: str, pos: int) -> list[float]:
    params = [float(match.group()) for match in _FLOAT_PATTERN.finditer(text, pos=pos)]
    if not params:
        raise cmn.ParseError(f"Surface parameters are not specified in '{text.strip()}'")
    return params


SURFACE_TYPES = {
    "P",
    "PX",
    "PY",
    "PZ",
    "S",
    "SO",
    "SX",
    "SY",
    "SZ",
    "CX",
    "CY",
    "CZ",
    "C/X",
    "C/Y",
    "C/Z",
    "KX",
    "KY",
    "KZ",
    "K/X",
    "K/Y",
    "K/Z",
    "TX",
    "TY",
    "TZ",
    "SQ",
    "GQ",
    "X",
    "Y",
    "Z",
    "RPP",
    "RCC",
    "BOX",
}


def intern_surface_type(word: str) -> str:
    word = cmn.ensure_upper(word)
    word, res = cmn.internalize(word, SURFACE_TYPES)
    if not res:
        raise cmn.ParseError(f"{word} is not a valid surface type")
    return word
