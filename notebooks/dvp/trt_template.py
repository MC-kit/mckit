import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys

    from pathlib import Path

    import numpy as np

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as mcw

    HOST = os.uname().nodename
    VERSION = "0.0.1"
    MODEL_DIR = mut.check_dir(Path("~/dev/mcnp/trt/wrk/models/2025/5.4.1").expanduser())
    LP_DIR = mut.check_dir(MODEL_DIR / "hall+trt-5.4.1.results/5.0/lp")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Выделение ячеек для исправления потерянных частиц
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(f"""
        - Python: {sys.version}, at {sys.prefix}
        - host: {HOST}
        - cwd: {Path.cwd()}
        - mckit: {mc.__version__}
        - script: {__file__}, {VERSION}
    """).callout()
    return


@app.cell
def _():
    model_path = mut.check_file(MODEL_DIR / "neutron-5.0.i")
    return (model_path,)


@app.cell
def _(model_path):
    tokamak_info = mc.from_file(model_path)
    return (tokamak_info,)


@app.cell
def _():
    cell_no_in_question = 299
    return (cell_no_in_question,)


@app.cell
def _():
    from itertools import chain

    def extract_suspicious_cells(cell_number: list[int], info: mc.ParseResult) -> list[mc.Body]:
        cells = list(info.cells_index[cell_no] for cell_no in cell_number)
        predicate = mcw.filter_by_shared_surfaces(cells)
        return list(chain(cells, mcw.extract_cells(info.universe, predicate)))

    return (extract_suspicious_cells,)


@app.cell
def _(cell_no_in_question, extract_suspicious_cells, tokamak_info):
    suspicious_cells = extract_suspicious_cells([cell_no_in_question], tokamak_info)
    return (suspicious_cells,)


@app.cell
def _(suspicious_cells):
    len(suspicious_cells)
    return


@app.cell
def _(suspicious_cells):
    universe = mc.Universe(suspicious_cells)
    return (universe,)


@app.cell
def _(cell_no_in_question, universe):
    universe.save(LP_DIR / f"lp-{cell_no_in_question}.i")
    return


@app.cell
def _():
    box_coords = [-181.893818174, 262.629482846, -219.476259394, -90.7423212671, 395.572382602, 219.476259394]
    return (box_coords,)


@app.cell
def _(box_coords):
    box = mc.Box.from_corners(np.array(box_coords[:3]), np.array(box_coords[3:]))
    return (box,)


@app.cell
def _(box):
    box
    return


@app.cell
def _(suspicious_cells, tokamak_info):
    suspicious_cells_numbers = list(mut.map_names(suspicious_cells))
    more_cells = list(
        mcw.extract_cells(
            tokamak_info.universe,
            mcw.filter_and(
                mcw.filter_by_surface_number(615),
                mcw.filter_by_surface_number(609),
                mcw.filter_not(mcw.filter_by_cell_numbers(suspicious_cells_numbers)),
            ),
        )
    )
    return (more_cells,)


@app.cell
def _(more_cells):
    more_cells
    return


@app.cell
def _(more_cells, suspicious_cells):
    more_cells_universe = mc.Universe(suspicious_cells + more_cells)
    return (more_cells_universe,)


@app.cell
def _(more_cells_universe):
    more_cells_universe.save(LP_DIR / "lp-299-1.i")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
