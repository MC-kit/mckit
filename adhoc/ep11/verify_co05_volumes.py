# noinspection GrazieInspection
"""Find ratio of a volume fo steel with Co0.5 fraction to other steel volume.

The model pc11_shields8_Co05.i is variant where the specific material was applied for
frame parts, which are in the integrator scope - fraction of Co was increased to 0.5%.
The material's id is 207302.
All other parts (diagnostics) use the same materials as in baseline model.

We want to show that the portion of the specific steel is much less than of other steel
and cannot affect SDDR value too much.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import os
import sqlite3 as sq
import sys

from pathlib import Path
from time import time_ns

import dotenv
import numpy as np
import pandas as pd
import typer

from loguru import logger
from tqdm import tqdm

from mckit.geometry import EX, EY, EZ, Box
from mckit.parser import ParseResult, from_file

if TYPE_CHECKING:
    from sqlite3 import Connection

    from mckit import Element, Material, Universe

dotenv.load_dotenv()

__version__ = "0.0.1"

DEBUG = os.getenv("MCKIT_DEBUG") is not None

LOG_FORMAT = os.getenv(
    "MCKIT_LOG_FORMAT",
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>",
)


def _init_logger(level="INFO", _format=LOG_FORMAT, log_path=None) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format=_format,
        level=level,
        backtrace=True,
        diagnose=True,
    )
    """Initialize logging to stderr and file."""
    if log_path:
        logger.add(log_path, backtrace=True, diagnose=True)


WRK_DIR = Path(os.getenv("MCKIT_MODEL", "~/dev/mcnp/ep11/wrk/pc/Co05-volumes")).expanduser()
if not WRK_DIR.is_dir():
    raise FileNotFoundError(WRK_DIR)

MODEL_PATH = WRK_DIR / "pc11_shields8_Co05.i"
if not MODEL_PATH.is_file():
    raise FileNotFoundError(MODEL_PATH)


def _from_bounds(
    minx: float, maxx: float, miny: float, maxy: float, minz: float, maxz: float
) -> Box:
    min_vals = np.array([minx, miny, minz])
    max_vals = np.array([maxx, maxy, maxz])
    if not np.all(min_vals < max_vals):
        raise ValueError("Unsorted boundaries values")
    center = 0.5 * (min_vals + max_vals)
    widths = max_vals - min_vals
    return Box(center, *widths, ex=EX, ey=EY, ez=EZ)


def create_global_box() -> Box:
    """Define the box surrounding the model.

    This cell 196000 with zero importance.
    Surfaces:
    206001:-206002:206003:206005:-206004:-206000
    206000 PX 830
    206001 PX 3350
    206002 PY -1200
    206003 PY 1200
    206004 PZ -620
    206005 PZ 740

    Returns:
        Box: box with the given boundaries
    """
    global_box = _from_bounds(830.0, 3350, -1200.0, 1200.0, -620, 740)
    logger.info("Global box volume: {}", global_box.volume)
    return global_box


def load_mcnp_model(model_path: Path = MODEL_PATH) -> ParseResult:
    """Load MCNP model.

    Args:
        model_path: path to the model

    Returns:
        ParseResult: Universe and indexes for cells, surfaces transformations and materials
    """
    logger.info("Loading model from {}", model_path)
    model_info = from_file(MODEL_PATH)
    model = model_info.universe
    logger.info("Loaded model with {} cells", len(model))
    return model_info


def _init_data_base(con: Connection) -> None:
    logger.info("Deleting the old tables")
    con.executescript(
        """
        drop table if exists cell_geometry;
        drop table if exists cell_material;
        drop table if exists material_mass;  -- use table not view, view is too slow
        """
    )
    logger.info("Creating tables cell_geometry and cell_material")
    con.executescript(
        """
        create table cell_material (
            cell int primary key,
            material int,
            density real,
            stp_path text
        );
        create table cell_geometry (
            cell int primary key,
            box_min_x real,
            box_max_x real,
            box_min_y real,
            box_max_y real,
            box_min_z real,
            box_max_z real,
            box_time  int,
            volume real,
            min_vol real,
            vol_time int
        );
        """
    )
    logger.info("Creating compositions and nuclides table")
    con.executescript(
        """
        drop table if exists nuclides;
        create table nuclides(
            charge int,
            mass_number int,
            isomer int,
            molar_mass real,
            primary key (charge, mass_number, isomer)
        );
        drop table if exists compositions;
        create table compositions(
            material_id int,
            molar_mass  real,
            total_mass  real,
            primary key (material_id)
        );
        drop table if exists composition_nuclides;
        create table composition_nuclides(
            material_id int,
            charge int,
            mass_number int,
            isomer int,
            lib text,
            fraction real,
            primary key (material_id, charge, mass_number, isomer, lib),
            foreign key (charge, mass_number, isomer) references nuclides (charge, mass_number, isomer),
            foreign key (material_id) references compositions (material_id)
        );
    """
    )
    logger.info("Creating view material_mass")
    con.executescript(
        """
        create table material_mass (
            material int primary key,
            mass real
        )
        """
    )
    logger.info("Database is initialized")


def _collect_model_info(model: Universe, con: Connection, global_box: Box, min_vol: float = 0.25):
    _init_data_base(con)
    for i, c in enumerate(tqdm(model)):
        m: Material = c.material()
        if m is not None:
            cell = c.name()
            material = m.composition.name()
            density = m.density
            con.execute(
                """
                insert into cell_material (
                    cell, material, density
                )
                values (?, ?, ?)
                """,
                (cell, material, density),
            )
            box_time = -time_ns()
            bounding_box = c.shape.bounding_box(box=global_box, tol=2.0)
            box_time += time_ns()
            (
                (box_min_x, box_max_x),
                (box_min_y, box_max_y),
                (box_min_z, box_max_z),
            ) = bounding_box.bounds
            logger.debug(
                "Added box for cell {}: {} {} {}, {}, {}",
                cell,
                box_min_x,
                box_max_x,
                box_min_y,
                box_max_y,
                box_min_z,
                box_max_z,
            )
            vol_time = -time_ns()
            volume = c.shape.volume(bounding_box, min_vol)
            vol_time += time_ns()
            con.execute(
                """
                insert into cell_geometry (
                    cell,
                    box_min_x, box_max_x, box_min_y, box_max_y, box_min_z, box_max_z, box_time,
                    volume, min_vol, vol_time
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cell,
                    box_min_x,
                    box_max_x,
                    box_min_y,
                    box_max_y,
                    box_min_z,
                    box_max_z,
                    box_time,
                    volume,
                    min_vol,
                    vol_time,
                ),
            )
            logger.debug(
                "Added volume for cell {}: {}, rel: {}",
                cell,
                volume,
                min_vol / volume if volume > 0 else 1.0,
            )
            # con.execute(
            #     """
            #     insert into material_mass
            #     select
            #         a.material,
            #         sum(volume * density) as mass
            #     from
            #     cell_material a
            #     inner join cell_geometry b on a.cell = b.cell
            #     group by
            #         a.material
            # """
            # )
            material_mass = pd.read_sql(
                """
                select
                    material,
                    sum(volume * density) mass
                from cell_material a
                inner join cell_geometry b
                    on a.cell = b.cell
                group by material
                """,
                con,
            )
            con.executemany(
                """
                update compositions
                set total_mass = ?
                where material_id = ?
                """,
                material_mass[["mass", "material"]].itertuples(index=False, name="mm"),
            )
            con.commit()
            if DEBUG and i > 2:
                break


app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def fill(
    db_path: Annotated[
        Path,
        typer.Option(
            help="Path to the sqlite database to be created",
        ),
    ] = WRK_DIR
    / "model-info.sqlite",
    model_path: Annotated[
        Path,
        typer.Option(
            help="Path to the input MCNP model",
        ),
    ] = WRK_DIR
    / "pc11_shields8_Co05.i",
) -> None:
    """Collect information from an MCNP model to database."""
    logger.info("Creating model info database {}", db_path)
    con = sq.connect(db_path)
    try:
        global_box = create_global_box()
        model_parse = load_mcnp_model(model_path)
        model = model_parse.universe
        _collect_model_info(model, con, global_box)
    finally:
        con.close()
    logger.success("The database {} is created", db_path)


@app.command()
def add_materials(
    db_path: Annotated[
        Path,
        typer.Option(
            help="Path to the sqlite database to be created",
        ),
    ] = WRK_DIR
    / "model-info.sqlite",
    model_path: Annotated[
        Path,
        typer.Option(
            help="Path to the input MCNP model",
        ),
    ] = WRK_DIR
    / "pc11_shields8_Co05.i",
) -> None:
    """Load material compositions and nuclides to the database."""
    logger.info("Adding  materials info database {}", db_path)
    con = sq.connect(db_path)
    try:
        model_parse = load_mcnp_model(model_path)
        model = model_parse.universe
        compositions = model.get_compositions()
        con.executemany(
            """
            insert into compositions (
                material_id,
                molar_mass
            ) values (
                ?, ?
            )
            """,
            (
                (
                    int(c.name()) if c.name() else 0,
                    c.molar_mass,
                )
                for c in compositions
            ),
        )
        con.commit()

        elements: set[Element] = set()
        elements.update(*(composition.elements() for composition in compositions))
        con.executemany(
            """
            insert into nuclides (
                charge,
                mass_number,
                isomer,
                molar_mass
            ) values (
                ?, ?, ?, ?
            )
            """,
            (
                (
                    element.charge,
                    element.mass_number,
                    element.isomer,
                    element.molar_mass,
                )
                for element in elements
            ),
        )
        con.commit()

        con.executemany(
            """
            insert into composition_nuclides (
                material_id,
                charge,
                mass_number,
                lib,
                isomer,
                fraction
            ) values (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                (
                    int(composition.name()) if composition.name() else 0,
                    element.charge,
                    element.mass_number,
                    element.lib,
                    element.isomer,
                    fraction,
                )
                for composition in compositions
                for element, fraction in composition
            ),
        )
        con.commit()

    finally:
        con.close()
    logger.success("The materials from {!r} are added to the database {!r}", model_path, db_path)


@app.command()
def analyze(
    db_path: Annotated[
        Path,
        typer.Option(
            help="Path to the sqlite database to be created",
        ),
    ] = WRK_DIR
    / "model-info.sqlite",
    suspicious: Annotated[
        int, typer.Option(help="Material id to find the mass ratio to total")
    ] = 207302,
) -> None:
    """Analyze the information on model.

    - Define ratio of a given "suspicious" material to total mass.
    """
    logger.info("Analyzing the MCNP model volumes.")
    con = sq.connect(db_path)
    try:
        total_cobalt_mass = (
            con.execute(
                """
            select
                sum(co_mass)
            from (
                select
                    c.material_id,
                    m.mass * cn.fraction * n.molar_mass / c.molar_mass co_mass
                from
                    material_mass m
                    inner join compositions c on c.material_id = m.material
                    inner join composition_nuclides cn on c.material_id = cn.material_id
                    inner join nuclides n on
                        cn.charge = n.charge and cn.mass_number = n.mass_number and cn.isomer = n.isomer
                where
                    n.charge = 27 and n.mass_number = 59 and n.isomer = 0
                order by co_mass
            );
            """
            ).fetchone()[0]
            * 0.001
        )
        """Total Co mass in materials in kg."""

        #     select
        #     sum(mass)
        #     total
        # from
        # material_mass
        # where
        # material in (
        #     select material_id from compositions where charge=27 and mass_number=59
        #
        #
        # -- Co mass fraction in materials
        # select
        # cn.material_id,
        # 100 * cn.fraction * n.molar_mass/c.molar_mass mass_fraction
        # from
        # compositions c
        # inner join composition_nuclides cn on c.material_id = cn.material_id
        # inner join nuclides n on
        # cn.charge = n.charge and cn.mass_number = n.mass_number and cn.isomer = n.isomer
        # where
        # n.charge = 27 and n.mass_number = 59 and n.isomer = 0
        # order by mass_fraction;
        #
        # select
        # m.material,
        # sum(m.mass * cn.fraction * n.molar_mass/c.molar_mass co_mass
        # from
        # material_mass m
        # inner join compositions c on c.material_id = m.material
        # inner join composition_nuclides cn on c.material_id = cn.material_id
        # inner join nuclides n on
        # cn.charge = n.charge and cn.mass_number = n.mass_number and cn.isomer = n.isomer
        # where
        # n.charge = 27 and n.mass_number = 59 and n.isomer = 0
        # order by co_mass;

        logger.info("Total mass of Co in materials {:3g}kg", total_cobalt_mass)

        # mass_207302_fetch = con.execute(
        #     """
        #     select mass from material_mass where material = ?
        #     """,
        #     (suspicious,),
        # ).fetchone()

        mass_co_in_207302_fetch = con.execute(
            """
            select
                sum(co_mass)
            from (
                select
                    c.material_id,
                    m.mass * cn.fraction * n.molar_mass / c.molar_mass co_mass
                from
                    material_mass m
                    inner join compositions c on c.material_id = m.material
                    inner join composition_nuclides cn on c.material_id = cn.material_id
                    inner join nuclides n on
                        cn.charge = n.charge and cn.mass_number = n.mass_number and cn.isomer = n.isomer
                where
                    n.charge = 27 and n.mass_number = 59 and n.isomer = 0
                    and
                    m.material = 207302
                order by co_mass
            );
            """
        ).fetchone()
        if mass_co_in_207302_fetch:
            mass_co_in_207302 = mass_co_in_207302_fetch[0] * 0.001
            """Mass of m207302 in kg."""
            logger.info("Mass of material 207302 {:3g}kg", mass_co_in_207302)

            ratio = mass_co_in_207302 / total_cobalt_mass

            logger.info("Ratio is {:3g}%", ratio * 100)
        else:
            logger.warning("Cannot find material {}")
    finally:
        con.close()
    logger.success("The database {} is analyzed", db_path)


@app.callback()
def start(
    log_path: Annotated[
        Path,
        typer.Option(help="Path to log file."),
    ] = WRK_DIR
    / "model-info.log"
) -> None:
    """Present information on MCNP cells volumes and masses."""
    _init_logger(log_path=log_path)
    logger.info("{}, v{}", Path(__file__).name, __version__)


if __name__ == "__main__":
    app()
