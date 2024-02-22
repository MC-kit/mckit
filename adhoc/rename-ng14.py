"""TODO..."""

from __future__ import annotations

from mckit import Universe
from mckit.parser import from_file


def main():
    """Set range of cell, surface and material numbers from 2000."""
    u = from_file("ng-14_v4.i").universe
    u.rename(start_surf=2000, start_cell=2000, start_mat=2000)
    new_cells = []
    for c in u:
        new_cells.append(c.simplify(min_volume=1e-2))
    new_u = Universe(new_cells)
    new_u.save("ng-14-v4-simplified.i")


if __name__ == "__main__":
    main()
