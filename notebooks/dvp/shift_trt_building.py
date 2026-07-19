import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")

with app.setup:
    from typing import Iterable

    import sys

    from pathlib import Path

    import numpy as np


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
    VERSION="0.1.1"
    OUT=ROOT / f".wrk/{Path(__file__).stem}/{VERSION}"
    return (OUT,)


@app.cell
def _(OUT, mc):
    mc.utils._path.make_dir(OUT)
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
    building = building_info.universe
    return (building,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    surface33 - поверхность пола в зале
    """)
    return


@app.cell
def _(building_info):
    surface33 = building_info.surfaces_index[33]
    return (surface33,)


@app.cell
def _(surface33):
    surface33
    return


@app.cell
def _(surface33):
    surface33.mcnp_repr()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Смотри замету в Zotero "Положение токамака ТРТ в здании" о связи систем координат токамака и здания.
    После смещения здания поверхность 33 должна стать PZ -583.5, чтобы опоры установки "почти касались" пола.
    """)
    return


@app.cell
def _():
    translation=np.array([-29, 1556, -589], dtype=np.float64)
    return (translation,)


@app.cell
def _(mc, translation):
    tr1 = mc.Transformation(translation=translation)
    return (tr1,)


@app.cell
def _(tr1):
    tr1.apply2point([0,0,0])
    return


@app.cell
def _(building, tr1):
    building_shifted = building.transform(tr1)
    return (building_shifted,)


@app.cell
def _(building_shifted):
    new_surfaces = building_shifted.get_surfaces()
    return (new_surfaces,)


@app.function
def find_surface(name: int, surfaces):
    return next((x for x in surfaces if x.name() == name), None)


@app.cell
def _(new_surfaces):
    new_surface33 = find_surface(33, new_surfaces)
    return (new_surface33,)


@app.cell
def _(new_surface33):
    new_surface33.mcnp_repr()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Поверхность 33 там, где нужно.
    """)
    return


@app.cell
def _(building_shifted):
    building_shifted._verbose_name = "hall-1.2.3-shifted"
    return


@app.cell
def _(OUT, building_shifted):
    building_shifted.save(OUT / "hall_shifted.mcnp")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
