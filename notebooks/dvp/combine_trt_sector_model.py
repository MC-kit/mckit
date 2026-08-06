import marimo

__generated_with = "0.23.16"
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
    VERSION = "0.1.0"
    MODEL_DIR = mut.check_dir(mut.mkpath("~/dev/mcnp/trt/wrk/models/2025/5.4.2-sector/").expanduser())


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
        - models: {MODEL_DIR}
    """).callout()
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Попутно разбираемся с потерянными частицами
    """)
    return


@app.cell
def _(s45_universe):
    cells_with_surf = list(mut.map_names(mcw.extract_cells(s45_universe, mcw.filter_by_surface_number(4))))
    cells_with_surf
    return


@app.cell
def _(s45_info):
    surf_graveyard = s45_info.surfaces_index[3719]
    return (surf_graveyard,)


@app.cell
def _(surf_graveyard):
    surf_graveyard.mcnp_repr()
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
    Все убранные ячейки и заменяем на -3719 (3 : -4).
    И оставляем сам graveyard.
    """)
    return


@app.cell
def _(surf_3, surf_4, surf_graveyard):
    half_space_3 = mc.Shape("C", surf_3)  # -3 C - complement
    half_space_4 = mc.Shape("S", surf_4)  # +4 S - same (identity)
    graveyard = mc.Shape("S", surf_graveyard)
    graveyard_complement = graveyard.complement()
    sector = mc.Shape("I", half_space_3, half_space_4, graveyard_complement)
    space_in_sector = mc.Shape("I", half_space_3, half_space_4)
    return (
        graveyard_complement,
        half_space_3,
        half_space_4,
        sector,
        space_in_sector,
    )


@app.function
def shape_str(c: mc.Shape):
    return "".join(c.get_words())


@app.cell
def _(sector):
    shape_str(sector)
    return


@app.cell
def _():
    return


@app.cell
def _(half_space_3, half_space_4):
    half_space_3_complement, half_space_4_complement = (x.complement() for x in (half_space_3, half_space_4))
    return half_space_3_complement, half_space_4_complement


@app.cell
def _(graveyard_complement, half_space_3_complement, half_space_4_complement):
    sector_gravyard_in = graveyard_complement.intersection(half_space_3_complement.union(half_space_4_complement))
    return (sector_gravyard_in,)


@app.cell
def _(half_space_3_complement, half_space_4_complement):
    space_out_of_sector = half_space_3_complement.union(half_space_4_complement)
    return (space_out_of_sector,)


@app.cell
def _(space_out_of_sector):
    shape_str(space_out_of_sector)
    return


@app.cell
def _(sector_gravyard_in):
    shape_str(sector_gravyard_in)
    return


@app.cell
def _(mo, s45_universe, space_in_sector, space_out_of_sector):
    def _():
        new_cells = []
        # max_check = 0
        as_is = []
        omitted = []
        intersected = []
        with mo.status.progress_bar(
            total=len(s45_universe),
            title="Buidling sector cells",
            show_eta=True,
            show_rate=True,
        ) as bar:
            for cell in s45_universe:
                # max_check += 1
                # if max_check > 100:
                #     break
                if cell.name() == 1880:  # graveyard
                    assert cell.is_graveyard
                    new_cells.add(cell)
                    continue
                out_intersection = cell.intersection(space_out_of_sector)
                out_simplified = out_intersection.simplify(min_volume=1)
                if out_simplified.is_empty:
                    new_cells.append(cell)  # to find cells relly needing intersection with space_in_sector
                    as_is.append(cell.name())
                else:
                    in_intersection = cell.intersection(space_in_sector)
                    in_simpified = in_intersection.simplify(min_volume=1)
                    if in_simpified.is_empty:
                        print("Cell ", cell.name(), " is out of sector and omitted")
                        omitted.append(cell.name())
                    else:
                        new_cells.append(in_simpified)
                        intersected.append(cell.name())
                bar.update(subtitle=f"as_is: {len(as_is)}, omitted: {len(omitted)}, intersected: {len(intersected)}")
        return new_cells, as_is, omitted, intersected

    new_cells, as_is, omitted, intersected = _()
    return (new_cells,)


@app.cell
def _(new_cells):
    list(mut.map_names(new_cells))
    return


@app.cell
def _():
    from mckit.cli.commands import do_split

    return (do_split,)


@app.cell
def _(do_split):
    def split_model(split_dir: Path, model_path: Path) -> None:
        split_dir.mkdir(parents=True, exist_ok=True)
        do_split(split_dir, model_path, override=True, separators=True)

    return (split_model,)


@app.cell
def _(split_model, tokamak_input_path):
    SPLIT_DIR = MODEL_DIR / "trt-5.4.split"
    split_model(SPLIT_DIR, tokamak_input_path)
    return (SPLIT_DIR,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Разделим еще файл cells.txt на ячейки установки и  "generated voids". Последние начинаются с ячейки 9016.
    """)
    return


@app.cell
def _(SPLIT_DIR):
    def _():
        cells_part_path = mut.check_file(SPLIT_DIR / "cells.txt")
        path_a = cells_part_path.parent / "cells-installation.txt"
        path_b = cells_part_path.parent / "cells-generated-voids.txt"
        text = cells_part_path.read_text()
        idx = text.find("\n9016")
        assert idx > 0
        path_a.write_text(text[: idx + 1])  # leava \n in the "installation" part
        path_b.write_text(text[idx + 1 :])

    _()
    return


@app.cell
def _(tokamak_input_path):
    tokamak_info = mc.from_file(tokamak_input_path)
    return (tokamak_info,)


@app.cell
def _(tokamak_info):
    tokamak = tokamak_info.universe
    return (tokamak,)


@app.cell
def _(tokamak):
    len(tokamak)
    return


@app.cell
def _(tokamak_info):
    tokamak_graveyard_in = tokamak_info.cells_index[16160]
    return (tokamak_graveyard_in,)


@app.cell
def _(tokamak_graveyard_in):
    tokamak_graveyard_in.options["comment"]
    return


@app.cell
def _(hall_cell, tokamak_graveyard_in):
    intersect_graveyard_in = hall_cell.intersection(tokamak_graveyard_in)
    return (intersect_graveyard_in,)


@app.cell
def _(hall_cell):
    hall_cell.shape.complexity()
    return


@app.cell
def _(intersect_graveyard_in):
    intersect_graveyard_in.shape.complexity()
    return


@app.cell
def _(intersect_graveyard_in):
    intersect_graveyard_in_simplified = simplify(intersect_graveyard_in)
    return (intersect_graveyard_in_simplified,)


@app.cell
def _(intersect_graveyard_in_simplified):
    intersect_graveyard_in_simplified
    return


@app.cell
def _(intersect_graveyard_in_simplified):
    intersect_graveyard_in_simplified.shape.complexity()
    return


@app.cell
def _(intersect_graveyard_in):
    hall_graveyard_in_intersection_universe = mc.Universe([intersect_graveyard_in])
    return (hall_graveyard_in_intersection_universe,)


@app.cell
def _(intersect_graveyard_in_simplified):
    hall_graveyard_in_intersectin_simplified_universe = mc.Universe([intersect_graveyard_in_simplified])
    return (hall_graveyard_in_intersectin_simplified_universe,)


@app.cell
def _(hall_graveyard_in_intersection_universe):
    hall_graveyard_in_intersection_universe.save(MODEL_DIR / "hall-graveyard-in-intersection.i")
    return


@app.cell
def _(hall_graveyard_in_intersectin_simplified_universe):
    hall_graveyard_in_intersectin_simplified_universe.save(MODEL_DIR / "hall-graveyard-in-intersection-simplified.i")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Проверить и скорректировать "generated void cells"
    """)
    return


@app.function
def generated_void(x):
    return 9016 <= x.name() < 16160


@app.cell
def _(tokamak):
    generated_voids_without_comment = list(
        mcw.extract_cells(
            tokamak,
            mcw.filter_and(generated_void, mcw.filter_not(mcw.filter_by_comment("Automatic Generated Void Cell"))),
        )
    )
    len(generated_voids_without_comment)
    return (generated_voids_without_comment,)


@app.cell
def _(generated_voids_without_comment):
    generated_voids_without_comment[0].options
    return


@app.cell
def _(tokamak):
    generated_voids = list(mcw.extract_cells(tokamak, generated_void))
    return (generated_voids,)


@app.cell
def _(generated_voids, mo, tokamak):
    mo.md(f"""
    {len(generated_voids)=}, {len(tokamak)=}
    """)
    return


@app.cell
def _(generated_voids):
    "\n".join(generated_voids[0].options["comment"])
    return


@app.cell
def _(generated_voids):
    generated_voids[0].original
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Проверим, не налезают ли generated voids на блок пола в здании
    """)
    return


@app.cell
def _(hall_info):
    floor_top_surface = hall_info.surfaces_index[30033]
    floor_top_surface.mcnp_repr()
    return (floor_top_surface,)


@app.cell
def _(floor_top_surface):
    hall_space = mc.Shape("S", floor_top_surface)
    hall_space.get_words()
    return (hall_space,)


@app.cell
def _(hall_space):
    under_floor_space = hall_space.complement()
    under_floor_space.get_words()
    return (under_floor_space,)


@app.cell
def _(under_floor_space):
    under_floor_space.test_points([[0, 0, -583.5062459 + 1], [0, 0, -583.5062460], [0, 0, -583.5062459 - 1]])
    return


@app.cell
def _(tokamak_input_path):
    path_to_save_intersected = tokamak_input_path.parent / "intersected-voids.csv"
    # path_to_save_intersected.unlink()
    return (path_to_save_intersected,)


@app.cell
def _(
    generated_voids,
    hall_space,
    mo,
    path_to_save_intersected,
    under_floor_space,
):
    def correct_generated_voids_intersecting_with_floor():
        corrected_voids = []
        intersected_names = []
        with mo.status.progress_bar(
            total=len(generated_voids),
            title="Проверяем есть ли пересечения 'generated_voids' c полом зала",
            show_eta=True,
            show_rate=True,
        ) as bar:
            if path_to_save_intersected.exists():
                prev_intersected_names = np.loadtxt(path_to_save_intersected, dtype=np.int32)
                known_intersection = set(prev_intersected_names)
            else:
                known_intersection = None
            for c in generated_voids:
                _name = c.name()
                if known_intersection and _name not in known_intersection:
                    corrected_voids.append(c)  # add not intersecting cell as is
                    bar.update(subtitle=f"✅ {_name} - skipped")
                else:
                    x = c.intersection(under_floor_space)
                    x = simplify(x)
                    if x.is_empty:
                        bar.update(subtitle=f"✅ {_name} - clear")
                        corrected_voids.append(c)  # add not intersecting cell as is
                    else:
                        bar.update(subtitle=f"❌ {_name} - intersects")
                        intersected_names.append(_name)
                        y = simplify(c.intersection(hall_space))
                        if not y.is_empty:
                            corrected_voids.append(y)

            if known_intersection and not known_intersection == set(intersected_names):
                msg = f"Known intersection file is obsolete, remove {path_to_save_intersected} and rerun"
                raise EnvironmentError(msg)
            return intersected_names, corrected_voids

    return (correct_generated_voids_intersecting_with_floor,)


@app.cell
def _(
    correct_generated_voids_intersecting_with_floor,
    path_to_save_intersected,
):
    intersected_names, corrected_voids = correct_generated_voids_intersecting_with_floor()
    np.savetxt(path_to_save_intersected, intersected_names, fmt="%d")
    return corrected_voids, intersected_names


@app.cell
def _(corrected_voids, generated_voids, intersected_names, mo):
    mo.md(f"""
    {len(generated_voids)=}, {len(intersected_names)=}, {len(corrected_voids)=}
    """)
    return


@app.cell
def _(SPLIT_DIR):
    corrected_voids_path = SPLIT_DIR / "generated-voids-for-hall-integration.txt"
    return (corrected_voids_path,)


@app.cell
def _(corrected_voids, corrected_voids_path):
    def _():
        with corrected_voids_path.open(mode="w") as fid:
            for c in corrected_voids:
                original = c.original
                if original is None:
                    print(c.mcnp_repr(), file=fid)
                    print("       $ corrected for hall integration", file=fid)
                else:
                    print(original, file=fid)

    _()
    return


@app.cell
def _(generated_voids, hall_space, mo):
    def correct_all_voids_without_simplification():
        corrected_voids = []
        with mo.status.progress_bar(
            total=len(generated_voids),
            title="Добавляем пересечение 'generated_voids' c пространством выше пола",
            show_eta=True,
            show_rate=True,
        ) as bar:
            for c in generated_voids:
                _name = c.name()
                y = c.intersection(hall_space)
                if not y.is_empty:
                    corrected_voids.append(y)
                bar.update()
        return corrected_voids

    return (correct_all_voids_without_simplification,)


@app.cell
def _(correct_all_voids_without_simplification):
    corrected_all_voids = correct_all_voids_without_simplification()
    return (corrected_all_voids,)


@app.cell
def _(SPLIT_DIR):
    corrected_all_voids_path = SPLIT_DIR / "all-voids-for-hall-integration.txt"
    return (corrected_all_voids_path,)


@app.cell
def _(corrected_all_voids, corrected_all_voids_path):
    def _():
        with corrected_all_voids_path.open(mode="w") as fid:
            print("c generated voids intersected with a space above hall", file=fid)
            for c in corrected_all_voids:
                print(c.mcnp_repr(), file=fid)

    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Utils
    """)
    return


@app.cell
def _():
    mc.box.GLOBAL_BOX
    return


@app.function
def simplify(cell: mc.Body) -> mc.Body:
    return cell.simplify(box=mc.box.Box(center=[0, 10, 0], wx=10000, wy=10000, wz=10000), min_volume=1)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
