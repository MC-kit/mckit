"""Utility code to use in all other modules."""

from __future__ import annotations

from mckit.utils.accept import TVisitor, accept, on_unknown_acceptor
from mckit.utils.io import MCNP_ENCODING
from mckit.utils.misc import (
    MAX_DIGITS,
    are_equal,
    compute_hash,
    deepcopy,
    filter_dict,
    get_decades,
    is_in,
    is_sorted,
    make_hashable,
    mids,
    prettify_float,
    round_array,
    round_scalar,
    significant_array,
    significant_digits,
)
from mckit.utils.resource import path_resolver
from mckit.utils.tolerance import FLOAT_TOLERANCE

__all__ = [
    "FLOAT_TOLERANCE",
    "MAX_DIGITS",
    "MCNP_ENCODING",
    "are_equal",
    "compute_hash",
    "deepcopy",
    "filter_dict",
    "get_decades",
    "make_hashable",
    "path_resolver",
    "round_array",
    "round_scalar",
    "significant_array",
    "significant_digits",
]
