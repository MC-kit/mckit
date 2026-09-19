import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys
    import time

    from pathlib import Path
    from textwrap import dedent

    import numpy as np

    from loguru import logger

    import mckit as mc
    import mckit.utils as mut
    import mckit.workflow as mcw

    from mckit.cli.commands import do_split

    HOST = os.uname().nodename
    VERSION = "0.1.2"
    MODEL_DIR = mut.check_dir(mut.mkpath("~/dev/mcnp/trt/wrk/models/2025/5.4.2-sector/").expanduser())
    min_vol_ratio = 1e-11
    WRK_DIR = mut.mkdir(MODEL_DIR / f"computed/{VERSION}-{min_vol_ratio}")

    logger.add(WRK_DIR / "combine_trt_sector_model.log")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Разработка геометрической части модели TRT 2025, 5.4.2-sector

    Входные файлы:
    - модель сектора s45.i (получена из результата mapstp и geouned) с небольшими модификциями (graveyard увеличе, sdef удален)

    Детали см. в Obsidian "Модель TRT 2025 5.4.2, сектор 45 градусов"

    TODO: перенести заметку сюда, по завершении работы.
    """)
    return


@app.cell
def _(INPUT_PATH, mo):
    INFO = f"""
        - Python: {sys.version}, at {sys.prefix}
        - host: {HOST}
        - cwd: {Path.cwd()}
        - mckit: {mc.__version__}
        - models: {MODEL_DIR}
        - script: {__file__}, {VERSION}
        - input: {INPUT_PATH}
        - wrkdir: {WRK_DIR.relative_to(MODEL_DIR)}
        - min_vol_ratio: {min_vol_ratio}
    """
    logger.info(INFO)
    mo.md(INFO).callout()
    return


@app.cell
def _():
    INPUT_PATH = mut.check_file(MODEL_DIR / "s45.i")
    return (INPUT_PATH,)


@app.cell
def _(INPUT_PATH):
    s45_info = mc.from_file(INPUT_PATH)
    return (s45_info,)


@app.cell
def _(s45_info):
    s45_universe = s45_info.universe
    return (s45_universe,)


@app.cell
def _(s45_universe):
    graveyard_cell = s45_universe[-1]
    return (graveyard_cell,)


@app.cell
def _(s45_universe):
    len(s45_universe)
    return


@app.cell
def _(graveyard_cell):
    graveyard_name = graveyard_cell.name()
    graveyard_name
    return (graveyard_name,)


@app.cell
def _(graveyard_cell):
    graveyard_box = graveyard_cell.shape.complement().bounding_box()
    return (graveyard_box,)


@app.cell
def _(graveyard_box):
    graveyard_box.bounds
    return


@app.cell
def _(graveyard_box, mo):
    mo.md(f"""
    global box volume: {graveyard_box.volume:.1g}
    """)
    return


@app.cell
def _():
    f"Min. volume ratio: {min_vol_ratio:.1g}"
    return


@app.cell
def _(graveyard_box):
    min_volume = graveyard_box.volume * min_vol_ratio
    min_volume
    return (min_volume,)


@app.cell
def _(graveyard_cell):
    graveyard_surf = next(graveyard_cell.shape.scan_surfaces())
    return (graveyard_surf,)


@app.cell
def _(graveyard_surf):
    graveyard_surf
    return


@app.cell
def _(graveyard_surf):
    graveyard_surf.mcnp_repr()
    return


@app.cell
def _(graveyard_surf):
    graveyard_surf_name = graveyard_surf.name()
    graveyard_surf_name
    return (graveyard_surf_name,)


@app.cell
def _(graveyard_surf, graveyard_surf_name, s45_info):
    graveyard_surf == s45_info.surfaces_index[graveyard_surf_name]
    return


@app.cell
def _(s45_info):
    surf_3 = s45_info.surfaces_index[3]
    return (surf_3,)


@app.cell
def _(surf_3):
    surf_3.mcnp_repr()
    return


@app.cell
def _(s45_info):
    surf_4 = s45_info.surfaces_index[4]
    return (surf_4,)


@app.cell
def _(surf_4):
    surf_4.mcnp_repr()
    return


@app.cell
def _():
    point = [1, 0, 0]
    return (point,)


@app.cell
def _(point, surf_3, surf_4):
    {x.name(): x.test_points(point)[0] for x in (surf_3, surf_4)}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Ячейки внутри сектора должны быть ограничены поверхностями -3 и +4.
    Если ячейка изначально не пересекается с этими поверхностями, то оставляем ее как есть.
    Если ячейка полностью выходят за пространство сектора, то убираем ее.
    Все убранные ячейки заменяем на sector_gravyard_in - пространство между выбранным сектором и graveyard. Спецификация: -3719 (3 : -4).
    И оставляем сам graveyard.
    """)
    return


@app.cell
def _(graveyard_cell, surf_3, surf_4):
    half_space_3 = mc.Shape("C", surf_3)  # -3 C - complement
    half_space_4 = mc.Shape("S", surf_4)  # +4 S - same (identity)
    graveyard = graveyard_cell.shape
    graveyard_complement = graveyard.complement()
    sector = mc.Shape("I", half_space_3, half_space_4, graveyard_complement)
    space_in_sector = mc.Shape("I", half_space_3, half_space_4)
    return graveyard_complement, half_space_3, half_space_4, space_in_sector


@app.function
def shape_str(c: mc.Shape):
    return "".join(c.get_words())


@app.cell
def _(space_in_sector):
    shape_str(space_in_sector)
    return


@app.cell
def _(half_space_3, half_space_4):
    half_space_3_complement, half_space_4_complement = (x.complement() for x in (half_space_3, half_space_4))
    return half_space_3_complement, half_space_4_complement


@app.cell
def _(half_space_3_complement, half_space_4_complement):
    space_out_of_sector = half_space_3_complement.union(half_space_4_complement)
    return (space_out_of_sector,)


@app.cell
def _(graveyard_complement, space_out_of_sector):
    sector_gravyard_in = graveyard_complement.intersection(space_out_of_sector)
    return (sector_gravyard_in,)


@app.cell
def _(space_out_of_sector):
    shape_str(space_out_of_sector)
    return


@app.cell
def _(sector_gravyard_in):
    shape_str(sector_gravyard_in)
    return


@app.cell
def _(
    graveyard_box,
    graveyard_name,
    min_volume,
    mo,
    s45_universe,
    space_in_sector,
    space_out_of_sector,
):
    def _():
        new_cells = []
        # max_check = 0
        as_is = []
        omitted = []
        intersected = []
        with mo.status.progress_bar(
            total=len(s45_universe) - 1,  # processing all the cells but graveyard
            title="Вычисляем ячейки модели",
            show_eta=True,
            show_rate=True,
        ) as bar:
            start_time = time.time()
            for cell in s45_universe:
                # max_check += 1
                # if max_check > 100:
                #     break
                if cell.name() == graveyard_name:  # graveyard
                    assert cell.is_graveyard
                    break  # no more cells after graveyard
                out_intersection = cell.intersection(space_out_of_sector)
                out_simplified = out_intersection.simplify(box=graveyard_box, min_volume=min_volume)
                if out_simplified.is_empty:
                    new_cells.append(cell)  # to find cells relly needing intersection with space_in_sector
                    as_is.append(cell.name())
                else:
                    in_intersection = cell.intersection(space_in_sector)
                    in_simpified = in_intersection.simplify(box=graveyard_box, min_volume=min_volume)
                    if in_simpified.is_empty:
                        omitted.append(cell.name())
                    else:
                        new_cells.append(in_simpified)
                        intersected.append(cell.name())
                bar.update(subtitle=f"as_is: {len(as_is)}, omitted: {len(omitted)}, intersected: {len(intersected)}")
            elapsed_time = time.time() - start_time
        return new_cells, as_is, omitted, intersected, elapsed_time

    new_cells, as_is, omitted, intersected, elapsed_time = _()
    return elapsed_time, new_cells, omitted


@app.cell(hide_code=True)
def _(elapsed_time):
    with (WRK_DIR / "min-vol-ratio-vs-elapsed.time.csv").open("a") as _f:
        print(VERSION, ",", min_vol_ratio, ",", elapsed_time, file=_f)
    return


@app.cell
def _(elapsed_time):
    logger.info("version: {}, min_vol_ratio: {}, elapsed_time: {}", VERSION, min_vol_ratio, elapsed_time)
    return


@app.cell
def _(omitted):
    logger.info("Omitted cells:\n {}", omitted)
    return


@app.cell
def _(new_cells):
    new_cells[-1]
    return


@app.cell
def _(new_cells):
    new_cells_len = len(list(mut.map_names(new_cells)))
    new_cells_len
    return


@app.cell
def _(new_cells):
    max_used_name = max(x.name() for x in new_cells)
    max_used_name
    return (max_used_name,)


@app.cell
def _(graveyard_name, max_used_name):
    if max_used_name + 1 < graveyard_name:
        sector_gravyard_in_name = max_used_name + 1
    else:
        sector_gravyard_in_name = graveyard_name + 1
    return (sector_gravyard_in_name,)


@app.cell
def _(sector_gravyard_in_name):
    sector_gravyard_in_name
    return


@app.cell
def _(graveyard_cell, new_cells, sector_gravyard_in, sector_gravyard_in_name):
    universe_cells = new_cells + [
        mc.Body(
            sector_gravyard_in,
            name=sector_gravyard_in_name,
            VOL=1.0,
            IMPN=1.0,  # keep non-zero importances for lost particles tests
            IMPP=1.0,
            comment=["Sector graveyard_in"],
        ),
        graveyard_cell,
    ]
    return (universe_cells,)


@app.cell
def _(universe_cells):
    sector_universe = mc.Universe(universe_cells)
    return (sector_universe,)


@app.cell
def _():
    sector_universe_path = WRK_DIR / f"s45c.i"
    return (sector_universe_path,)


@app.cell
def _(sector_universe, sector_universe_path):
    sector_universe.save(sector_universe_path)
    return


@app.cell
def _(sector_universe_path):
    with sector_universe_path.open("a") as _f:
        _f.write(
            dedent(
                """\
            MODE P
            VOID 
            NPS 1e6
            PRDMP 2J -1
            C SDEF PAR=P X=D1 Y=D2 Z=D3 
            C SI1 -1.0000000e+00 7.1990889e+02 
            C SI2 -2.7620090e+02 2.7602312e+02 
            C SI3 -5.8446004e+02 6.4380699e+02 
            C SP1 0  1 
            C SP2 0  1 
            C SP3 0  1 
            SDEF PAR=P NRM=-1 SUR=3719 WGT=1.9066061e+06 DIR=d1
            SI1 0 1
            SP1 -21 1
            F4:P  1262    
        """
            )
        )
    return


@app.cell
def _():
    lp = 3
    nps = 1e8
    lpr = lp / nps
    logger.info("lp: {}, at nps {} lpr: {:.2g}", lp, nps, lpr)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Уменьшение min_volume в 10 раз не улушило, а даже немного ухудшило результ. При этом времени на расчет потрачено больше чем в два раза.

    Исправил клэш ячеек 208,214 и перенес результат в исходный s45.i.

    Получил очень хороший результат: lpr 3e-8.
    Продолжаем с этой моделью.

    Делаем split s45.i и готовим модель для сборки со sdef tally, meshtally.
    """)
    return


@app.function
def split_model(split_dir: Path, model_path: Path) -> None:
    split_dir.mkdir(parents=True, exist_ok=True)
    do_split(split_dir, model_path, override=True, separators=True)


@app.cell
def _(sector_universe_path):
    SPLIT_DIR = WRK_DIR / "split"
    split_model(SPLIT_DIR, sector_universe_path)
    return


@app.cell
def _():
    s45_old_path = mut.check_file(mut.mkpath("~/dev/mcnp/trt/wrk/models/2025/5.0/trt-sector-45/s45.i").expanduser())
    return (s45_old_path,)


@app.cell
def _(s45_old_path):
    SPLIT_DIR_OLD = WRK_DIR / "split.old"
    split_model(SPLIT_DIR_OLD, s45_old_path)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Utils
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _simplify(graveyard_box, min_volume):
    def simplify(cell: mc.Body) -> mc.Body:
        return cell.simplify(box=graveyard_box, min_volume=min_volume)

    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
