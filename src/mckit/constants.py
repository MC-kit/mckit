"""Shared constants."""

from __future__ import annotations

import numpy as np

__all__ = [
    "FLOAT_TOLERANCE",
    "MIN_BOX_VOLUME",
    "RESOLUTION",
]

MIN_BOX_VOLUME = 0.001

# Resolution of float number
RESOLUTION = np.finfo(float).resolution

FLOAT_TOLERANCE = 1.0e-12
