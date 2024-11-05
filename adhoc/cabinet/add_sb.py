#!/bin/python

"""Add collimator to trt-4.0 model.

The collimator is to be added to EP12 port.

Cells to subtract from:
    - 1214 - extension case
    - 1179 - envelope,
    - 2253, 2040 - void spaces behind
    - 1133, 1149, 1165 - DFW (1, 2, 3)
    - 1433 - empty space in VV in front of EP
"""
from __future__ import annotations

from typing import Final

import os
import sqlite3 as sq

# noinspection PyPackageRequirements
import numpy as np

from config import file_field

# noinspection PyPackageRequirements
from pydantic import BaseModel, FilePath

# noinspection PyPackageRequirements
from rich.console import Console

from mckit import Universe, Transformation
from mckit.box import Box
from mckit.parser import from_file

console = Console()

TRT_4_CELL_COUNT: Final[int] = 4407
"""Number of cells in original TRT model with collimator, v4."""

SB_CELL_CNT: Final[int] = 8
"""Cells with materials from Shielding Box model."""

VARIANT2_Z_SHIFT: Final[float] = 533.6
"""Shift up over Z axis for the second variant."""

VARIANT2_TR: Final[Transformation] = Transformation(translation=[0.0, 0.0, VARIANT2_Z_SHIFT])

# SB cells centers (for MCNP comin file):
#
# -42.8 908.1 -605.2
# 42.8 908.1 -605.2
# -42.8 964.2 -605.2
# 42.8 964.2 -605.2
# 0.0 950.0 -530.0
# 0.0 950.0 -530.0
# 0.0 936.0 -530.0
# 0.0 936.0 -530.0


class Config(BaseModel):
    """Configuration."""

    sb_path: FilePath = file_field("./trt-sb-v1.i")
    trt_path: FilePath = file_field("./neutron-4.1.i")


def create_box_from_opposite_vertices(v1, v2) -> Box:
    """Create box with given coordinates of opposite vertices.

    Assuming the edges of the box are aligned with EX, EY, EZ.

    Args:
        v1: vertex 1
        v2: ... the opposite

    Returns:
        Box created from corners coordinates
    """
    v1, v2 = (np.asarray(x, dtype=float) for x in (v1, v2))
    center = 0.5 * (v1 + v2)
    sizes = np.abs(v2 - v1)
    return Box(center, *sizes)


def update_sql(cfg: Config) -> None:
    sb_sql = cfg.sb_path.with_suffix(".sqlite")
    trt_sql = cfg.trt_path.with_suffix(".sqlite")
    sb_con: sq.Connection = sq.connect(sb_sql)
    trt_con: sq.Connection = sq.connect(trt_sql)
    trt_con.executemany(
        """
        insert into cells (
            cell,
            volume,      -- volume computed by SpaceClaim
            xmin,        -- bounding box boundaries
            ymin,
            zmin,

            xmax,
            ymax,
            zmax,
            path
        )
        values(?, ? , ? , ?, ?,  ?, ?, ?, ?)
        """,
        sb_con.execute(
            """
            select
                cell + 4407 cell, -- to start from 4408
                volume,      -- volume computed by SpaceClaim
                xmin,        -- bounding box boundaries
                ymin,
                zmin,

                xmax,
                ymax,
                zmax,
                path
            from cells
            order by cell
            """
        ).fetchall(),
    )
    trt_con.commit()
    trt_con.close()
    sb_con.close()


def load_box(con: sq.Connection, cell: int) -> Box | None:
    fetched = con.execute(
        """
        select xmin, ymin, ymax, xmax, ymax, zmax from cells where cell=?
        """,
        (cell,),
    ).fetchone()

    if fetched is None:
        return None

    xmin, ymin, zmin, xmax, ymax, zmax = fetched
    return create_box_from_opposite_vertices([xmin, ymin, zmin], [xmax, ymax, zmax])


def main() -> None:
    """Add shielding box to trt-4.0 model."""
    os.chdir("/home/dvp/dev/mcnp/trt/wrk/models/2024/cabinet/stp/Model materials/edited_egor")
    cfg = Config()
    sb_sql = cfg.sb_path.with_suffix(".sqlite")
    trt_sql = cfg.trt_path.with_suffix(".sqlite")
    sb_con: sq.Connection = sq.connect(sb_sql)
    trt_con: sq.Connection = sq.connect(trt_sql)
    change_log = cfg.trt_path.with_suffix(".changed-cells.txt")

    sb_parse = from_file(cfg.sb_path)
    sb_model = list(filter(lambda x: 1 <= x.name() <= SB_CELL_CNT, sb_parse.universe))
    trt_parse = from_file(cfg.trt_path)
    trt_model = trt_parse.universe
    new_cells = []

    with change_log.open("w") as fid:
        for _c in trt_model:
            c = _c
            trt_box = load_box(trt_con, c.name())
            changed = False
            for cc in sb_model:
                sb_box = load_box(sb_con, cc.name())
                if sb_box is None:
                    msg = f"Cannot find data for cell # {cc.name()}"
                    raise ValueError(msg)
                if trt_box is None or trt_box.check_intersection(sb_box):
                    c = c.intersection(cc.shape.complement())
                    changed = True
            if changed:
                c = c.simplify(min_volume=1e-2)
                if c.shape.is_empty():
                    console.print("Deleted cell", c.name(), style="red")
                    print(c.name(), "deleted", file=fid)
                else:
                    console.print("Updated cell", c.name(), style="green")
                    print(c.name(), "changed", file=fid)
                    new_cells.append(c)
            else:
                new_cells.append(c)
    sb_con.close()
    trt_con.close()
    new_cells.extend(sb_model)
    with_sb = Universe(new_cells)
    with_sb.save(cfg.trt_path.parent / "trt-4.0-with-sb.i")


if __name__ == "__main__":
    # update_sql(Config())
    main()
