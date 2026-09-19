import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")

with app.setup:
    from typing import Iterable

    import os
    import sys

    from pathlib import Path

    import numpy as np

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as muw

    HOST = os.uname().nodename
    VERSION="1.2.4-shifted+renamed"
    WRK_DIR = Path("/home/dvp/dev/mcnp/trt-hall/model/1.2-walls-split")
    assert WRK_DIR.is_dir()
    OUT= WRK_DIR / f"{VERSION}"
    META=f"""
    - Python: {sys.version}, at {sys.prefix}
    - host: {HOST}
    - cwd: {WRK_DIR}
    - mckit: {mc.__version__}
    - script: {__file__}, {VERSION}
    """


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(META)
    return


@app.cell
def _():
    mut.mkdir(OUT)
    return


@app.cell
def _():
    INPUT_PATH = mut.check_file(WRK_DIR / "1.2.1/hall.i")
    return (INPUT_PATH,)


@app.cell
def _(INPUT_PATH):
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
def _(translation):
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
    building_shifted.rename(start_cell=30001, start_surf=30001)
    return


@app.cell
def _(building_shifted):
    new_surfaces = building_shifted.get_surfaces()
    return (new_surfaces,)


@app.function
def find_surface(name: int, surfaces):
    return next((x for x in surfaces if x.name() == name), None)


@app.cell
def _(new_surfaces):
    new_surface33 = find_surface(30000+33, new_surfaces)
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
    building_shifted._verbose_name = f"hall-{VERSION}"
    return


@app.cell
def _():
    out_path = Path(OUT, "hall.mcnp")
    return (out_path,)


@app.cell
def _(building_shifted, out_path):
    building_shifted.save(out_path)
    return


@app.cell
def _():
    from mckit.cli.commands import do_split

    return (do_split,)


@app.cell
def _(do_split, out_path):
    split_dir = OUT / "hall.split"
    split_dir.mkdir(parents=True, exist_ok=True)
    do_split(
        split_dir,
        out_path,
        override = True,
        separators = True
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Create "void" model to check lost particles
    """)
    return


@app.cell
def _(out_path):
    void_path = out_path.parent / "void.i"
    return (void_path,)


@app.cell
def _(out_path):
    text = out_path.read_text()
    text = text.replace(
        "\n30047 S 164.72711 1077.98071 995.8373 403930.81",
        "\n30047 S 164.72711 1077.98071 995.8373 4039.3081"
    )

    text += """\
    MODE P
    VOID 
    NPS 1e8
    PRDMP 2J -1
    C SDEF PAR=P X=D1 Y=D2 Z=D3 
    C SI1 -2.3392729e+03 2.7267271e+03 
    C SI2 -3.0115045e+03 2.0554659e+03
    C SI3 -1.0270625e+02 3.2723808e+03 
    C SP1 0  1 
    C SP2 0  1 
    C SP3 0  1 
    SDEF PAR=P NRM=-1 SUR=30047 WGT=5.1258257e+07 DIR=d1
    SI1 0 1
    SP1 -21 1
    F4:P  
          30001 30002 30003 30004 30005 30006 30007 
          30008 30009 30010 30011 30012 30013 30014 30015 
    C Cell volume normalization is set in cell cards VOL
    """
    return (text,)


@app.cell
def _(text, void_path):
    void_path.write_text(text)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
