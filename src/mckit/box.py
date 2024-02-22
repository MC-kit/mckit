"""Python subclass for geometry.Box."""

from __future__ import annotations

import numpy as np

from numpy.typing import NDArray

# noinspection PyUnresolvedReferences,PyPackageRequirements
from mckit.geometry import EX, EY, EZ
from mckit.geometry import GLOBAL_BOX as _GLOBAL_BOX
from mckit.geometry import Box as _Box
from mckit.utils import make_hashable


class Box(_Box):
    """Extend geometry.Box."""

    def __init__(self, center, wx, wy, wz, ex=EX, ey=EY, ez=EZ):
        _Box.__init__(self, center, wx, wy, wz, ex=ex, ey=ey, ez=ez)

    @classmethod
    def from_geometry_box(cls, geometry_box: _Box) -> Box:
        """Initialize python Box from geometry.Box.

        Args:
            geometry_box: source

        Returns:
            The new Box.
        """
        wx, wy, wz = geometry_box.dimensions
        return cls(
            geometry_box.center,
            wx,
            wy,
            wz,
            ex=geometry_box.ex,
            ey=geometry_box.ey,
            ez=geometry_box.ez,
        )

    @classmethod
    def from_corners(cls, min_corner: NDArray, max_corner: NDArray) -> Box:
        """Initialize from min and max corners.

        Args:
            min_corner: min corner
            max_corner: max ...

        Raises:
            ValueError: if min and max corners are not in order

        Returns:
            The new Box.
        """
        if not np.all(min_corner < max_corner):
            raise ValueError("Unsorted boundaries values")
        center = 0.5 * (min_corner + max_corner)
        widths = max_corner - min_corner
        wx, wy, wz = widths
        return cls(center, wx, wy, wz, ex=EX, ey=EY, ez=EZ)

    @classmethod
    def from_bounds(
        cls, minx: float, maxx: float, miny: float, maxy: float, minz: float, maxz: float
    ) -> Box:
        """Initialize Box from bounds.

        Args:
            minx: min x
            maxx: max x
            miny: min y
            maxy: max y
            minz: min z
            maxz: max z

        Returns:
            A new Box.
        """
        min_corner = np.array([minx, miny, minz])
        max_corner = np.array([maxx, maxy, maxz])
        return cls.from_corners(min_corner, max_corner)

    def __repr__(self):
        exm = "" if np.array_equal(self.ex, EX) else f"ex={self.ex}"
        eym = "" if np.array_equal(self.ey, EY) else f"ey={self.ey}"
        ezm = "" if np.array_equal(self.ez, EZ) else f"ez={self.ez}"
        msgs = [x for x in [exm, eym, ezm] if x]
        emsg = ", " + ", ".join(msgs) if msgs else ""
        wx, wy, wz = self.dimensions
        return f"Box({self.center}, {wx}, {wy}, {wz}{emsg})"

    def __eq__(self, other):
        return (
            np.array_equal(self.center, other.center)
            and np.array_equal(self.dimensions, other.dimensions)
            and np.array_equal(self.ex, other.ex)
            and np.array_equal(self.ey, other.ey)
            and np.array_equal(self.ez, other.ez)
        )

    def __hash__(self):
        return hash(make_hashable((self.center, self.dimensions, self.ex, self.ey, self.ez)))

    def __getstate__(self):
        center = self.center
        wx, wy, wz = self.dimensions
        ex = self.ex
        ey = self.ey
        ez = self.ez
        return center, wx, wy, wz, ex, ey, ez

    def __setstate__(self, state):
        center, wx, wy, wz, ex, ey, ez = state
        self.__init__(center, wx, wy, wz, ex, ey, ez)


GLOBAL_BOX = Box.from_geometry_box(_GLOBAL_BOX)
