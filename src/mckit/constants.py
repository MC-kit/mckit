"""Shared constants."""

from __future__ import annotations

import numpy as np

__all__ = [
    "MIN_BOX_VOLUME",
    "RESOLUTION",
    "FLOAT_TOLERANCE",
    "MCNP_ENCODING",
    "DROP_OPTIONS",
]

MIN_BOX_VOLUME = 0.001

# Resolution of float number
RESOLUTION = np.finfo(float).resolution

FLOAT_TOLERANCE = 1.0e-12

MCNP_ENCODING = "cp1251"

DROP_OPTIONS = frozenset(["original", "transform", "comment", "trailing_comment", "comment_above"])
