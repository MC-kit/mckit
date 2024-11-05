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

from mckit import Body, Transformation, Universe
from mckit.box import Box
from mckit.cli.logging import init_logger, logger
from mckit.parser import from_file

__version__ = "0.2.1"

TRT_4_CELL_COUNT: Final[int] = 4407
"""Number of cells in original TRT model with collimator, v4."""

TRT_4_SURF_COUNT: Final[int] = 4430
"""The last number of surfaces in original TRT model with collimator, v4."""

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
                (cell + ?) as cell, -- to start from 4408
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
            """,
            (TRT_4_CELL_COUNT + 1,),
        ).fetchall(),
    )
    trt_con.commit()
    trt_con.close()
    sb_con.close()


def load_box(con: sq.Connection, cell: int, z_shift: float = 0.0) -> Box | None:
    fetched = con.execute(
        """
        select xmin, ymin, zmin, xmax, ymax, zmax from cells where cell=?
        """,
        (cell,),
    ).fetchone()

    if fetched is None:
        return None

    xmin, ymin, zmin, xmax, ymax, zmax = fetched
    return create_box_from_opposite_vertices(
        [xmin, ymin, zmin + z_shift], [xmax, ymax, zmax + z_shift]
    )


def combine_models(
    SB_START_CELL: int,
    sb_con: sq.Connection,
    sb_model: list[Body],
    trt_cells_to_intersect,
    trt_con: sq.Connection,
    trt_model: Universe,
    z_shift: float = 0.0,
) -> list[Body]:
    new_cells: list[Body] = []

    for _c in trt_model:
        c = _c
        trt_box = load_box(trt_con, c.name())
        changed = False
        if c.name() in trt_cells_to_intersect:
            for cc in sb_model:
                bb_no = cc.name() - SB_START_CELL + 1
                sb_box = load_box(sb_con, bb_no, z_shift)
                if sb_box is None:
                    msg = f"Cannot find bounding box for SB cell # {bb_no}"
                    logger.error(msg)
                    raise ValueError(msg)
                if trt_box is None or trt_box.check_intersection(sb_box):
                    intersection = c.intersection(cc.shape).simplify(min_volume=1e-2)
                    if not intersection.shape.is_empty():
                        c = c.intersection(cc.shape.complement())
                        changed = True
        if changed:
            c = c.simplify(min_volume=1e-2)
            if c.shape.is_empty():
                logger.warning("Deleted cell {}", c.name())
            else:
                logger.info("Updated cell {}", c.name())
                new_cells.append(c)
        else:
            new_cells.append(c)

    new_cells.extend(sb_model)

    return new_cells


def main() -> None:
    """Add shielding box to trt-4.0 model."""
    os.chdir("/home/dvp/dev/mcnp/trt/wrk/models/2024/cabinet/stp/Model materials/edited_egor")
    init_logger("add-sb.log", False, True)
    logger.info("mckit/adhoc/add_sb, v{}", __version__)
    cfg = Config()
    sb_sql = cfg.sb_path.with_suffix(".sqlite")
    trt_sql = cfg.trt_path.with_suffix(".sqlite")
    sb_con: sq.Connection = sq.connect(sb_sql)
    trt_con: sq.Connection = sq.connect(trt_sql)

    trt_cells_to_intersect = {2040, 2328, 2253}

    logger.info("Loading SB model from {}", cfg.sb_path)
    sb_parse = from_file(cfg.sb_path)
    sb_universe = sb_parse.universe
    SB_START_CELL = TRT_4_CELL_COUNT + 1
    SB_START_SURF = TRT_4_SURF_COUNT + 1
    sb_universe.rename(start_cell=SB_START_CELL, start_surf=SB_START_SURF)
    sb_model = list(
        filter(lambda x: SB_START_CELL <= x.name() < SB_START_CELL + SB_CELL_CNT, sb_universe)
    )
    sb_universe2 = sb_universe.transform(VARIANT2_TR)
    sb_model2 = list(
        filter(lambda x: SB_START_CELL <= x.name() < SB_START_CELL + SB_CELL_CNT, sb_universe2)
    )
    logger.info("Loading TRT model from {}", cfg.trt_path)
    trt_parse = from_file(cfg.trt_path)
    trt_model = trt_parse.universe

    logger.info("Computing variant #1")

    new_cells = combine_models(
        SB_START_CELL, sb_con, sb_model, trt_cells_to_intersect, trt_con, trt_model
    )

    logger.info("Computing variant #2 (with Z-shift)")

    new_cells2 = combine_models(
        SB_START_CELL,
        sb_con,
        sb_model2,
        trt_cells_to_intersect,
        trt_con,
        trt_model,
        z_shift=VARIANT2_Z_SHIFT,
    )

    sb_con.close()
    trt_con.close()

    with_sb = Universe(new_cells)
    out = cfg.trt_path.parent / "trt-4.0-with-sb.i"
    with_sb.save(out)

    with_sb2 = Universe(new_cells2)
    out2 = cfg.trt_path.parent / "trt-4.0-with-sb2.i"
    with_sb2.save(out2)

    logger.success("The integrated models are saved in {} and {}(with Z-shift)", out, out2)


if __name__ == "__main__":
    # update_sql(Config())
    main()
