"""Fix lost particles in TRT v.7 model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

from collections.abc import Iterator
from pathlib import Path

import numpy as np

from tqdm import tqdm

from mckit import Body, Universe
from mckit.box import Box
from mckit.parser import from_file

if TYPE_CHECKING:
    from numpy.typing import NDArray


def create_box_from_opposite_vertices(v1: NDArray, v2: NDArray) -> Box:
    """Create box with given coordinates of opposite vertices.

    Assuming the edges of the box are aligned with EX, EY, EZ.

    Args:
        v1: vertex 1
        v2: ... the opposite

    Returns:
    """
    center = 0.5 * (v1 + v2)
    sizes = np.abs(v2 - v1)
    return Box(center, *sizes)


min_x, max_x, min_y, max_y, min_z, max_z = -859.0, 859.0, -859.0, 859.0, -532.0, 802.0
"""Coordinates of planes forming "The outer cell"."""
bottom_left_front = np.array([min_x, min_y, min_z], dtype=float)
top_right_rear = np.array([max_x, max_y, max_z], dtype=float)
outer_box = create_box_from_opposite_vertices(bottom_left_front, top_right_rear)

model_parse = from_file("trt-5.0-tag.i")

model = model_parse.universe

leaking_cells = [2173, 1607]

cell1607: Body = model_parse.cells_index[1607]
cell1607_box = cell1607.shape.bounding_box(tol=10, box=outer_box)

cell2173: Body = model_parse.cells_index[2173]
cell2173_box = cell2173.shape.bounding_box(tol=10, box=outer_box)

con = sq.connect("lost-particles.sqlite")
# con.execute(
#     """
#     create table if not exists cell_bounding_box (
#         cell int primary key,
#         cx real not null,
#         cy real not null,
#         cz real not null,
#         wx real not null,
#         wy real not null,
#         wz real not null
#     )
#     """
# )


def collect_bounding_boxes(
    con: sq.Connection,
    cells_index: dict[int, Body],
) -> Iterator[tuple[int, float, float, float, float, float, float]]:
    def _collect(
        _index: dict[int, Body],
    ):
        for cell in tqdm(sorted(_index.keys())):
            cell_box = _index[cell].shape.bounding_box(tol=10, box=outer_box)
            cx, cy, cz = cell_box.center
            wx, wy, wz = cell_box.dimensions
            yield cell, cx, cy, cz, wx, wy, wz

    cur = con.cursor()
    cur.executemany(
        """
        insert into cell_bounding_box (
            cell, cx, cy, cz, wx, wy, wz
        )
        values(?, ?, ?, ?, ?, ?, ?)
        """,
        _collect(cells_index),
    )
    con.commit()


def load_bounding_box(cell, con) -> Box:
    cx, cy, cz, wx, wy, wz = con.execute(
        """
        select cx, cy, cz, wx, wy, wz
        from cell_bounding_box
        where cell = ?
        """,
        (cell,),
    ).fetchone()
    return Box(np.array([cx, cy, cz], dtype=float), wx, wy, wz)


def define_cell_boxes_intersecting_with(box, cells_index, con) -> Iterator[int]:
    for c in cells_index.keys():
        cbox = load_bounding_box(c, con)
        if box.check_intersection(cbox):
            yield c


cells_potentially_intersecting_with_2173 = sorted(
    define_cell_boxes_intersecting_with(cell2173_box, model_parse.cells_index, con)
)


def load_cells_in(cell: int, con: sq.Connection) -> list[int]:
    return [
        x[0]
        for x in con.cursor()
        .execute(
            """
            select distinct cell_in cell from lost_particles
            where cell_fail = ?
            order by cell
            """,
            (cell,),
        )
        .fetchall()
    ]


def load_cells_in_for_leaking_cells(leaking_cells, con) -> dict[int, list[int]]:
    return {c: load_cells_in(c, con) for c in leaking_cells}


cells_in_for_leaking_cells = load_cells_in_for_leaking_cells(leaking_cells, con)

print("Fixing leaking cells")
new_cells = []
for c in tqdm(model):
    if c in cells_in_for_leaking_cells:
        cells_in = cells_in_for_leaking_cells[c]
        for ci in cells_in:
            ci_body = model_parse.cells_index[ci]
            cint = c.intersection(ci_body).simplify(min_volume=1e-2, box=outer_box)
            if cint.shape.is_empty():
                continue
            c = c.intersection(ci_body.complement()).simplify(min_volume=1e-2, box=outer_box)
    new_cells.append(c)

new_universe = Universe(new_cells)
new_universe.save("trt-5.0-lp-2.i")


def main():
    """TODO..."""


if __name__ == "__main__":
    main()
