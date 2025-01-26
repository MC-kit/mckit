"""Utility code to use in all other modules."""

from __future__ import annotations

from mckit.utils._io import (
    MCNP_ENCODING,
    check_if_all_paths_exist,
    check_if_path_exists,
    make_dir,
    make_dirs,
)
from mckit.utils._resource import path_resolver
from mckit.utils.accept import TVisitor, accept, on_unknown_acceptor
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
from mckit.utils.tolerance import FLOAT_TOLERANCE

__all__ = [
    "FLOAT_TOLERANCE",
    "MAX_DIGITS",
    "MCNP_ENCODING",
    "are_equal",
    "check_if_all_paths_exist",
    "check_if_path_exists",
    "compute_hash",
    "deepcopy",
    "filter_dict",
    "get_decades",
    "make_dir",
    "make_dirs",
    "make_hashable",
    "path_resolver",
    "round_array",
    "round_scalar",
    "significant_array",
    "significant_digits",
]
