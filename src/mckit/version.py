"""Provide package version and other meta information."""

from __future__ import annotations

try:
    import importlib_metadata as meta
except ImportError:
    import importlib.metadata as meta  # type: ignore

__title__ = "mckit"
__distribution__ = meta.distribution(__title__)
__meta_data__ = __distribution__.metadata
__author__ = __meta_data__["Author"]
__author_email__ = __meta_data__["Author-email"]
__license__ = __meta_data__["License"]
__summary__ = __meta_data__["Summary"]
__copyright__ = "Copyright 2018-2020 Roman Rodionov"  # TODO dvp: move to meta (project.toml)
__version__ = __distribution__.version
