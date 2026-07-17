import marimo

import mckit.utils._path

__generated_with = "0.23.14"
app = marimo.App(width="medium")

with app.setup:
    import sys

    from pathlib import Path


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(HOST, mo):
    mo.md(f"""
        - Python: {sys.version}, at {sys.prefix}
        - host: {HOST}
        - cwd: {Path.cwd()}
    """).callout()
    return


@app.cell
def _():
    import mckit as mc

    return (mc,)


@app.cell
def _():
    from nb_common.config_utils import HOST, check_file

    return HOST, check_file


@app.cell
def _(mc):
    ROOT = mc.utils.find_git_root_dir()
    return (ROOT,)


@app.cell
def _(ROOT):
    VERSION="0.1.0"
    OUT=ROOT / f".wrk/{Path(__file__).stem}/{VERSION}"
    return (OUT,)


@app.cell
def _(OUT, mc):
    mckit.utils._path.make_dir(OUT)
    return


@app.cell
def _(check_file):
    INPUT_PATH = check_file("/home/dvp/dev/mcnp/trt-hall/model/1.2-walls-split/1.2.1/hall.i")
    return (INPUT_PATH,)


@app.cell
def _(INPUT_PATH, mc):
    building_info = mc.from_file(INPUT_PATH)
    return (building_info,)


@app.cell
def _(building_info):
    tr1 = building_info.transformations[0]
    return (tr1,)


@app.cell
def _(tr1):
    tr1.apply2point([0,0,0])
    return


@app.cell
def _(tr1):
    tr_reversed = tr1.reverse()
    return (tr_reversed,)


@app.cell
def _(tr1, tr_reversed):
    tr_reversed.apply2transform(tr1).apply2point([0,0,0])
    return


@app.cell
def _(building_info, tr_reversed):
    new_universe = building_info.universe.transform(tr_reversed)
    return (new_universe,)


@app.cell
def _(new_universe):
    new_universe._verbose_name = "hall-1.2.3-shifted"
    return


@app.cell
def _(OUT, new_universe):
    new_universe.save(OUT / "hall_shifted.mcnp")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
