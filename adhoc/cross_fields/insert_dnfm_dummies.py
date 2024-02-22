"""Insert dummies of DNFM to stend model.

Use cell 1000 as envelop.
"""

from __future__ import annotations

from mckit import Transformation, Universe
from mckit.parser import from_file

building_parse_result = from_file("building-with-far-envelop.i")
building = building_parse_result.universe
envelop_cell = building_parse_result.cells_index[1000]
ng14_parse_result = from_file("../ng14/v4/ng-v4-tag.i")
ng14 = ng14_parse_result.universe
ng14tr = Transformation(
    translation=[297.5, 556.8, 165], rotation=[0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0]
)  # rotating tube to down direction
ng14_tr = ng14.transform(ng14tr)


ing07_parse_result = from_file("../ing-07/v4/ing-07-v4-tag.i")
ing07 = ing07_parse_result.universe
ing07tr = Transformation(
    translation=[297.5, 506.8, 165], rotation=[1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]
)  # rotating generator to positive y-axis direction
ing07_tr = ing07.transform(ing07tr)

universes_to_insert = [ng14_tr, ing07_tr]

new_cells = building.cells[:-1]


for u in universes_to_insert:
    for c in u:
        print(c.name())
        if c.material():
            envelop_cell = envelop_cell.intersection(c.shape.complement())

envelop_cell = envelop_cell.simplify(min_volume=1e-2)
new_cells.append(envelop_cell)

for u in universes_to_insert:
    new_cells.extend(c for c in u.cells if c.material())


new_universe = Universe(new_cells)
new_universe.save("../stend/ng14-ing07.i")


def main() -> None:
    """Insert envelop for generators NG14 and ING-07 into building model."""


if __name__ == "__main__":
    main()
