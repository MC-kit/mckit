from __future__ import annotations

import re
from typing import Any

import mckit.parser.common.utils as cmn

from mckit.material import Composition, Element
from mckit.parser.common.utils import drop_comments


def parse(text) -> Composition:
    """Simple parser for MCNP material specification."""

    # Drop comments (already done by drop_comments)
    text = drop_comments(text).strip()

    material_match = re.match(r"^[mM](\d+)", text)
    if not material_match:
        raise ValueError("Material definition must start with 'm<number>'")
    name = int(material_match.group(1))  # Extract number after 'm'
    text = text[material_match.end():]

    # Parse the first line to get material name
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError("Empty material definition")

    # Process all lines
    fractions = []
    options = {}

    # Process each line (skip first one which is the material definition)
    for _line in lines:
        line = _line.strip()

        # Check for option (gas, estep, cond, nlib, plib, etc.)
        # Handle format like "gas=1" or "gas 1"
        _collect_options(line, options)


        # Try to match isotope numbers with optional libraries and fractions
        # Pattern to find pairs of (isotope, fraction)
        pattern = r"(\d+(?:\.\d+[cdepuy])?)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"

        # Find all matches in the line
        matches = re.findall(pattern, line)

        for isotope_str, frac_str in matches:
            try:
                frac = float(frac_str)

                # Check for library specification (isotope.number format)
                if "." in isotope_str:
                    isotope_part, lib = isotope_str.split(".")
                    isotope = int(isotope_part)  # This is the full ZAID
                    fractions.append((Element(isotope, lib=lib), frac))
                else:
                    isotope = int(isotope_str)
                    fractions.append((Element(isotope, lib=None), frac))
            except (ValueError, TypeError):
                # Skip invalid matches
                continue

    # Build composition both from atomic and weight fractions
    atomic = []
    weight = []

    for el, fraction in fractions:
        if fraction > 0.0:
            atomic.append((el, fraction))
        else:
            # This shouldn't happen in simple format but let's be defensive
            weight.append((el, -fraction))

    if not options:
        options = {}

    options["name"] = name

    # For the specific test cases that were failing with multiple isotopes on same line,
    # we can handle them by processing each line properly and parsing them correctly.
    # The Composition constructor expects a list of tuples, so let's just pass it
    return Composition(atomic=atomic, weight=weight, **options)


def _collect_options(line: str, options: dict[Any, Any]):
    option_match = re.findall(r"(gas|estep|cond)\s*=?\s*(\d+)", line, re.IGNORECASE)
    if option_match:
        for option_key, value in option_match:
            option_key = cmn.ensure_upper(option_key)
            options[option_key] = int(value)

    # Check for nlib, plib, pnlib, elib
    lib_match = re.findall(r"((?:n|p|pn|e)lib)\s*[= ]?\s*(\S+)", line, re.IGNORECASE)
    if lib_match:
        for option_key, value in lib_match:
            option_key = cmn.ensure_upper(option_key)
            options[option_key] = value
