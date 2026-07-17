"""Utility code to use in all other modules."""

from __future__ import annotations

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

from ._path import (
    check_if_all_paths_exist,
    check_if_path_exists,
    find_git_root_dir,
    has_subdir,
    make_dir,
    make_dirs,
    search_path_upward,
)
from .named import HasName, Name, check_name_is_int, default_name_key, map_names

__all__ = [
    "FLOAT_TOLERANCE",
    "MAX_DIGITS",
    "HasName",
    "Name",
    "TVisitor",
    "accept",
    "are_equal",
    "check_if_all_paths_exist",
    "check_if_path_exists",
    "check_name_is_int",
    "compute_hash",
    "deepcopy",
    "default_name_key",
    "filter_dict",
    "find_git_root_dir",
    "get_decades",
    "has_subdir",
    "is_in",
    "is_sorted",
    "make_dir",
    "make_dirs",
    "make_hashable",
    "map_names",
    "mids",
    "on_unknown_acceptor",
    "path_resolver",
    "prettify_float",
    "round_array",
    "round_scalar",
    "search_path_upward",
    "significant_array",
    "significant_digits",
]
