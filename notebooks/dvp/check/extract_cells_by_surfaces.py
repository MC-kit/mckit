import marimo

__generated_with = "0.23.16"
app = marimo.App()

with app.setup:
    # Initialization code that runs before all other cells
    from typing import Sequence

    import sys
    from pathlib import Path

    import mckit as mc
    import mckit.workflow as mwf
    import mckit.utils as mut

    from mckit import Universe, Box, Body, Shape
    from mckit.cli import init_logger, logger

    __version__ = "0.2.1"
    MODEL_DIR = mut.check_dir(mut.mkpath("~/dev/dsf/lp14/").expanduser())
    OUTPUT_PREFIX = mut.mkdir(MODEL_DIR / f"50-assets/20-output/{__version__}")
    OUTPUT_PREFIX.mkdir(parents=True, exist_ok=True)

    def out_name(fname: str) -> Path:
        return OUTPUT_PREFIX / fname

    def extract_suspicious_universe(tokamak_complex, suspicious_surfaces: list[int]) -> Universe:
        cells = mwf.extract_cells(tokamak_complex, mwf.filter_by_surface_numbers(suspicious_surfaces))
        return mwf.make_universe(cells)

    def save_suspicious_universe(universe: Universe, suspicious_surfaces: list[int]) -> None:
        suspicious_universe_path = out_name(f"suspicios-{"+".join(str(s) for s in suspicious_surfaces)}.mcnp")
        universe.save(suspicious_universe_path)
        logger.info(
            "Saved universe for suspicious surfaces {} in ",
            suspicious_surfaces,
            suspicious_universe_path.absolute(),
        )

    init_logger(out_name("mckit.log"), quiet=False, verbose=False)
    logger.info("Script cut_sector.py, version {}", __version__)
    logger.info("Extracting sector")
    logger.info("Using mckit {}", mc.__version__)
    logger.info("Working dir: {}", Path.cwd())
    logger.info("Python {}, at {}", sys.version, sys.prefix)
    logger.info("Output files will be saved in {}", OUTPUT_PREFIX)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Extract cells related to suspicios surfaces from building model
    """)
    return


@app.cell
def _():
    tokamak_complex_path = mut.check_file(MODEL_DIR / "20251013101844_input.i")
    _path = Path(tokamak_complex_path)
    logger.info("Tokamak complex model file: {}", _path.absolute())
    logger.info("            ... model size: {}", _path.stat().st_size)
    return (tokamak_complex_path,)


@app.cell
def _(tokamak_complex_path):
    tokamak_complex_info = mc.from_file(tokamak_complex_path, encoding="cp1251")
    return (tokamak_complex_info,)


@app.cell
def _(tokamak_complex_info):
    logger.info(
        "Cells to process from tokamak complex {}", len(tokamak_complex_info.cells)
    )
    return


@app.cell
def _(mo):
    mo.md(f"""
    Reading rate: {239727 / (36):.0f} cell/min
    """)
    return


@app.cell
def _(tokamak_complex_info):
    tokamak_complex = tokamak_complex_info.universe
    return (tokamak_complex,)


@app.cell
def _(tokamak_complex):
    logger.info("Top level cells: {}", len(tokamak_complex))
    return


@app.cell
def _():
    suspicious_surfaces = [742009, 893384, 896469]
    return (suspicious_surfaces,)


@app.cell
def _(suspicious_surfaces, tokamak_complex):
    suspicious_universe = extract_suspicious_universe(tokamak_complex, suspicious_surfaces)
    save_suspicious_universe(suspicious_universe, suspicious_surfaces)
    return (suspicious_universe,)


@app.cell
def _(suspicious_universe):
    len(suspicious_universe)
    return


@app.cell
def _(cells, suspicious_surfaces, tokamak_complex):
    cells1 = list(mwf.extract_cells(tokamak_complex, mwf.filter_by_surface_numbers(suspicious_surfaces)))
    len(cells)
    return


@app.cell
def _(cells, suspicious_surfaces, tokamak_complex):
    cells2 = list(mwf.extract_cells(tokamak_complex, mwf.filter_by_surface_number(suspicious_surfaces[2])))
    len(cells)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
