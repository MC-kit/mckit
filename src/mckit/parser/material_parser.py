from __future__ import annotations

from typing import Any

import re

import mckit.parser.common.utils as cmn

from mckit import Composition, Element
from mckit.material import Composition, Element
from mckit.parser.common.utils import drop_comments


def parse(text: str) -> Composition:
    """Parse  MCNP material specification.

    Parameters
    ----------
    text : str
        Material specification.

    Returns
    -------
    Composition: representation of an MCNP material.

    Raises
    ------
    ValueError: on invalid material definition.
    """
    text = drop_comments(text).strip()
    name, pos = _extract_number(text)
    options = _collect_options(text, pos)
    return _create_composition(_extract_fractions(text, pos), name, options)


def _create_composition(
    fractions: list[tuple[Element, float]], name: int, options: dict[str, int | str]
) -> Composition:
    atomic = []
    weight = []
    for el, fraction in fractions:
        if fraction > 0.0:
            atomic.append((el, fraction))
        else:
            weight.append((el, -fraction))
    return Composition(atomic=atomic, weight=weight, name=name, **options)


_FRACTION_PATTERN = re.compile(
    r"(?P<zai>\d+)(?:\.(?P<lib>\S+))?\s+(?P<frac>[-+0-9eE.]+)", re.DOTALL
)


def _extract_fractions(text: str, pos: int) -> list[tuple[Element, float]]:
    return [_create_element(match) for match in _FRACTION_PATTERN.finditer(text, pos=pos)]


def _create_element(match: re.Match) -> tuple[Element, float]:
    isotope = match.group("zai")
    lib = match.group("lib")
    frac_str = match.group("frac")
    return Element(int(isotope), lib=lib), float(frac_str)


_MATERIAL_LABEL_PATTERN = re.compile(r"^[mM](\d+)")


def _extract_number(text: str) -> tuple[int, int]:
    if material_match := _MATERIAL_LABEL_PATTERN.match(text):
        name = int(material_match.group(1))
        return name, material_match.end() + 1
    raise ValueError("Material definition must start with 'm<number>'")


def _collect_options(text: str, pos: int) -> dict[str, str | int]:
    options: dict[str, str | int] = {}
    _collect_int_option(text, pos, options)
    _collect_str_option(text, pos, options)
    return options


_STR_OPTION_PATTERN = re.compile(r"((?:n|p|pn|e)lib)\s*=?\s*(\S+)", re.IGNORECASE)


def _collect_str_option(text: str, pos: int, options: dict[Any, Any]):
    """Check for nlib, plib, pnlib, elib."""
    if lib_match := _STR_OPTION_PATTERN.findall(text, pos=pos):
        for _option_key, value in lib_match:
            option_key = cmn.ensure_upper(_option_key)
            options[option_key] = value


_INT_OPTION_PATTERN = re.compile(r"(gas|estep|cond)\s*=?\s*(\d+)", re.IGNORECASE)


def _collect_int_option(text: str, pos: int, options: dict[Any, Any]):
    if option_match := _INT_OPTION_PATTERN.findall(text, pos=pos):
        for _option_key, value in option_match:
            option_key = cmn.ensure_upper(_option_key)
            options[option_key] = int(value)
