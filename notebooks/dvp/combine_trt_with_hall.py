import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys

    from pathlib import Path

    import mckit as mc
    import mckit.workflow as mcw

    HOST = os.uname().nodename


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Сборка интегральной модели ТРТ+зал

    Известно, что geouned добавляет в модель две ячейки:
    - graveyard_in пространство между "tokamak envelop" до внешней сферы
    - grave_yard - все за внешней сферой.

    "tokamak envelop" - пространство, занятое компонентами установки и "generated void", включающих эти компоненты

    Если предположить, что tokamak envelop, полностью умещается в ячейку #15 (экспериментальный зал", то при интеграции нужно вычесть из "зала" "envelop" и в конец модели здания добавить ячейки из модели установки. При этом переименовать ячейки и поверхности в добавляемой модели с удобным сдвигом (например, 100).

    Возможно, ситуация, чуть сложнее, если tokamak envelop выходит за пределы зала. В этом случае он пересекается с ячейкой #14 ("floor"-пол). В этом случае, нужно будет определить . ячейки, пересекающися с полом и вычесть из них все, что ниже верхней границы пола - поверхность 33. Таких ячеек не должно быть много и все они "void generated". Ячейки, не пересекающиеся с полом, нужно сохранить в модели неизменными.

    Поскольку затронутых этой интеграцией ячеек не много, а mckit пока не сохраняет исходный код ячеек в выдаче, можно вычислить измененные ячейки и добавить их в итоговую модель вручную или простым скриптом замены этих ячеек (TODO: добавить такую обработку в команду mckit concat).

    ## Ячейки, требующие внимания

    ### Здание

    - 14 - floor
    - 15 - hall

    ### Установка

    - 16160 - graveyard_in
    - 16161 - graveyard
    - ячейки "Automatic Generated Void Cell" (с этим комменатарием) - проверить не налезают ли они на floor
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
    """).callout()
    return


@app.cell
def _():
    ROOT = mc.utils.find_git_root_dir()
    return


@app.cell
def _():
    VERSION = "0.1.1"
    # OUT=ROOT / f".wrk/{Path(__file__).stem}/{VERSION}"
    return


@app.cell
def _():
    INPUT_PATH = Path("/home/dvp/dev/mcnp/trt-hall/model/1.2-walls-split/1.2.3-shifted/hall_shifted.mcnp")
    assert INPUT_PATH.is_file()
    return (INPUT_PATH,)


@app.cell
def _(INPUT_PATH):
    hall_info = mc.from_file(INPUT_PATH)
    return (hall_info,)


@app.cell
def _(hall_info):
    hall = hall_info.universe
    return


@app.cell
def _(hall_info):
    hall_cell = hall_info.cells_index[15]
    return (hall_cell,)


@app.cell
def _(hall_cell):
    hall_cell.options
    return


@app.cell
def _(hall_info):
    floor_cell = hall_info.cells_index[14]
    return (floor_cell,)


@app.cell
def _(floor_cell):
    floor_cell.options
    return


@app.cell
def _():
    tokamak_input_path = Path("/home/dvp/dev/mcnp/trt/wrk/models/2025/5.4.1/trt-5.4.0.i")
    assert tokamak_input_path.is_file()
    return (tokamak_input_path,)


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
    tokamak.rename(start_cell=100, start_surf=100)
    return


@app.cell
def _(tokamak):
    len(tokamak)
    return


@app.cell
def _(tokamak_info):
    tokamak_graveyard_in = tokamak_info.cells_index[16160]
    return (tokamak_graveyard_in,)


@app.cell
def _(hall_info):
    max_hall_cell_number = max(hall_info.cells_index.keys())
    max_hall_cell_number
    return


@app.cell
def _(hall_info):
    max_hall_surf_number = max(hall_info.surfaces_index.keys())
    max_hall_surf_number
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Номер ячеек и поверхностей установки сдвинем на 100.
    """)
    return


@app.cell
def _(tokamak_graveyard_in):
    tokamak_graveyard_in.options["comment"]
    return


@app.cell
def _(hall_cell, tokamak_graveyard_in):
    intersect_graveyard_in = hall_cell.intersection(tokamak_graveyard_in)
    return (intersect_graveyard_in,)


@app.cell
def _(intersect_graveyard_in):
    intersect_graveyard_in.shape.complexity()
    return


@app.function
def simplify(cell: mc.Body) -> mc.Body:
    return cell.simplify(box=mc.box.Box(center=[0, 10, 0], wx=10000, wy=10000, wz=10000), min_volume=1)


@app.cell
def _(intersect_graveyard_in):
    intersect_graveyard_in_simplified = simplify(intersect_graveyard_in)
    return (intersect_graveyard_in_simplified,)


@app.cell
def _():
    mc.box.GLOBAL_BOX
    return


@app.cell
def _(intersect_graveyard_in_simplified):
    intersect_graveyard_in_simplified.shape.complexity()
    return


@app.cell
def _(intersect_graveyard_in_simplified):
    intersect_graveyard_in_simplified
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
    hall_graveyard_in_intersection_universe.save(
        "/home/dvp/dev/mcnp/trt/wrk/models/2025/5.4.1/hall-graveyard-in-intersection.i"
    )
    return


@app.cell
def _(hall_graveyard_in_intersectin_simplified_universe):
    hall_graveyard_in_intersectin_simplified_universe.save(
        "/home/dvp/dev/mcnp/trt/wrk/models/2025/5.4.1/hall-graveyard-in-intersection-simplified.i"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Проверить и скорректировать "generated void cells"
    """)
    return


@app.cell
def _(tokamak):
    generated_voids = list(mcw.extract_cells(tokamak, mcw.filter_by_comment("Automatic Generated Void Cell")))
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Проверим, не налезают ли generated voids на блок пола в здании
    """)
    return


@app.cell
def _(hall_info):
    floor_top_surface = hall_info.surfaces_index[33]
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
    under_floor_space.test_points([[0, 0, -583.5062459+1], [0, 0, -583.5062460], [0, 0, -583.5062459-1]])
    return


@app.cell
def _(generated_voids, hall_space, mo, under_floor_space):
    def _():
        corrected_voids = []
        intersected_names = []
        with mo.status.progress_bar(
            total=len(generated_voids),
            title="Проверяем есть ли персечения 'generated_voids' c полом зала",
            show_eta=True,
            show_rate=True,
        ) as bar:
            for c in generated_voids:
                x = c.intersection(under_floor_space)
                x = simplify(x)
                if x.is_empty:
                    bar.update(subtitle=f"✅ {x.name()} - clear")
                    corrected_voids.append(c)  # add not intersecting cell as is
                else:
                    _n = x.name()
                    bar.update(subtitle=f"❌ {_n} - intersects")
                    intersected_names.append(_n)
                    y = simplify(c.intersection(hall_space))
                    if not y.is_empty:
                        corrected_voids.append(y)

        return intersected_names, corrected_voids

    intersected_names, corrected_voids = _()


    return corrected_voids, intersected_names


@app.cell
def _(corrected_voids, generated_voids, intersected_names, mo):
    mo.md(f"{len(generated_voids)=}, {len(intersected_names)=}, {len(corrected_voids)=}")
    return


@app.cell
def _(intersected_names):
    min(intersected_names), max(intersected_names)
    return


@app.cell
def _(generated_voids):
    min(x.name() for x in generated_voids), max(x.name() for x in generated_voids)
    return


@app.cell(hide_code=True)
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
