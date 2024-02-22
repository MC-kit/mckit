"""Insert envelop for generators NG14 and ING-07 into building model."""

from __future__ import annotations

from mckit import Body, Universe
from mckit.parser import from_file

building_parse_result = from_file("building.i")
building = building_parse_result.universe
envelop_parse_result = from_file("far-envelope.i")
envelop = envelop_parse_result.universe
envelop_cell: Body = envelop[0]
complement = envelop_cell.shape.complement()

new_cells = []

for c in building:  # type: Body
    if c.name() >= 166:  # cells "void reach"
        cint = envelop_cell.intersection(c).simplify(min_volume=0.01)
        if cint.shape.is_empty():
            new_cell = c
        else:
            new_cell = c.intersection(complement).simplify(min_volume=0.01)
            assert not new_cell.shape.is_empty()
        new_cells.append(new_cell)
    else:
        new_cells.append(c)  # "normal" cells

new_cells.append(envelop_cell)

new_universe = Universe(new_cells)
new_universe.save("building-with-far-envelop.i")


def main() -> None:
    """Insert envelop for generators NG14 and ING-07 into building model."""


if __name__ == "__main__":
    main()
