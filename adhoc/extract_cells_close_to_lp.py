"""Extract cells close to 'lost particle' event.

For a given cell 'c' extracts cells having at least one surface from 'c'.
The result is saved as separte model, having just a few cells. 

It's possible to specifiy several suspicious cells.

"""
from typing import Iterable


import sys

from pathlib import Path


from cyclopts import App

from mckit import Body, Universe
from mckit.body import Card
from mckit.parser import from_file


# !ls


Path.cwd()


cell_numbers_to_select = [187246]


# !ls


original_model_path = Path("pc11-1.1/pc11.i")
assert original_model_path.exists()


original_model = from_file(original_model_path)


original_universe = original_model.universe


len(original_universe)


selected_cells: list[Body] = [c for c in original_universe if c.name() in cell_numbers_to_select]


len(selected_cells)


selected_surfaces = set()
for c in selected_cells:
    selected_surfaces.update(c._shape.get_surfaces())


len(selected_surfaces)


adjacent_cells: list[Body] = [c for c in original_universe if c.name() not in cell_numbers_to_select and c._shape.get_surfaces() & selected_surfaces]


len(adjacent_cells)



def list_names(cards: list[Card]) -> Iterable[int]:
    return (c.name() for c in cards)



sorted(list_names(adjacent_cells))


new_cells = sorted(selected_cells + adjacent_cells, key=Body.name)


list(list_names(new_cells))


len(new_cells)


selected_universe = Universe(new_cells)


selected_universe.save("pc11-1.1/lp/selected.i")


# !ls pc11-1.1/lp


sorted(list_names(selected_surfaces))


clashed_surface_numbers: set[int] = set([201392])


cells_with_clashed_surfaces: list[Body] = [c for c in original_universe if set(s.name() for s in c._shape.get_surfaces()) & clashed_surface_numbers]


sorted(list_names(cells_with_clashed_surfaces))
