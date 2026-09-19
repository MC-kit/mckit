"""Provide package version and other meta information."""

from __future__ import annotations

import importlib.metadata as meta

__title__ = "mckit"
__distribution__ = meta.distribution(__title__)
__copyright__ = "Copyright 2018-2026 ITER RF DA"  # TODO @dvp: move to meta (project.toml)
__version__ = __distribution__.version
