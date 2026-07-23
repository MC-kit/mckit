import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")

with app.setup:
    import os
    import sys

    from pathlib import Path

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
    """).callout()
    return


@app.cell
def _():
    import mckit as mc

    return (mc,)


@app.cell
def _(mc):
    ROOT = mc.utils.find_git_root_dir()
    return


@app.cell
def _():
    VERSION="0.1.1"
    # OUT=ROOT / f".wrk/{Path(__file__).stem}/{VERSION}"
    return


@app.cell
def _():
    INPUT_PATH = Path("/home/dvp/dev/mcnp/trt-hall/model/1.2-walls-split/1.2.3-shifted/hall_shifted.mcnp")
    assert INPUT_PATH.is_file()
    return (INPUT_PATH,)


@app.cell
def _(INPUT_PATH, mc):
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
def _(mc, tokamak_input_path):
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
def _(intersect_graveyard_in):
    intersect_graveyard_in.shape.complexity()
    return


@app.cell
def _(mc):
    def simplify(cell: mc.Body) -> mc.Body:
        return cell.simplify(box = mc.box.Box(center=[0,10,0], wx=10000,wy=10000,wz=10000), min_volume=1)

    return (simplify,)


@app.cell
def _(intersect_graveyard_in, simplify):
    intersect_graveyard_in_simplified = simplify(intersect_graveyard_in)
    return (intersect_graveyard_in_simplified,)


@app.cell
def _(mc):
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
def _(intersect_graveyard_in, mc):
    hall_graveyard_in_intersection_universe = mc.Universe([intersect_graveyard_in])
    return (hall_graveyard_in_intersection_universe,)


@app.cell
def _(intersect_graveyard_in_simplified, mc):
    hall_graveyard_in_intersectin_simplified_universe = mc.Universe([intersect_graveyard_in_simplified])
    return (hall_graveyard_in_intersectin_simplified_universe,)


@app.cell
def _(hall_graveyard_in_intersection_universe):
    hall_graveyard_in_intersection_universe.save("/home/dvp/dev/mcnp/trt/wrk/models/2025/5.4.1/hall-graveyard-in-intersection.i")
    return


@app.cell
def _(hall_graveyard_in_intersectin_simplified_universe):
    hall_graveyard_in_intersectin_simplified_universe.save("/home/dvp/dev/mcnp/trt/wrk/models/2025/5.4.1/hall-graveyard-in-intersection-simplified.i")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Проверить "generated void cells"
    """)
    return


@app.cell
def _(mc):
    def contains_comment(cell: mc.Body, text: str)->bool:
        comment = cell.options.get("comment")
        if not comment:
            return False
        return any(lambda x: text in x and (print(text, "in", x) or True) for x in comment)


    return (contains_comment,)


@app.cell
def _(contains_comment, mc):
    def select_generated_voids_predicate(cell: mc.Body) -> bool:
        return contains_comment(cell, "Automatic Generated Void Cell")


    return (select_generated_voids_predicate,)


@app.cell
def _(select_generated_voids_predicate, tokamak):
    from mckit.workflow import extract_cells

    generated_voids = extract_cells(tokamak, select_generated_voids_predicate, add_surface_sharing_cells=False)
    return


@app.cell
def _(select_generated_voids_predicate, tokamak):
    generated_voids2 = [x for x in tokamak if select_generated_voids_predicate(x)]
    return (generated_voids2,)


@app.cell
def _(generated_voids2, tokamak):
    len(generated_voids2), len(tokamak)
    return


@app.cell
def _(generated_voids2):
    "\n".join(generated_voids2[0].options["comment"])
    return


@app.cell
def _(generated_voids2, select_generated_voids_predicate):
    select_generated_voids_predicate(generated_voids2[0])
    return


@app.cell
def _(contains_comment, generated_voids2):
    contains_comment(generated_voids2[0], "Automatic Generated Void Cell")
    return


@app.cell
def _(tokamak_info):
    tokamak_16159 = tokamak_info.cells_index[16159]
    return (tokamak_16159,)


@app.cell
def _(tokamak_16159):
    tokamak_16159.options["comment"]
    return


@app.cell
def _(floor_cell, tokamak_16159):
    check_16159 = floor_cell.intersection(tokamak_16159)
    return (check_16159,)


@app.cell
def _(check_16159):
    check_16159.shape.complexity()
    return


@app.cell
def _(check_16159, mc):
    check_16159_simplified =check_16159.simplify(mc.box.Box([0,10,0], 10000,10000,10000), min_volume=1)
    return (check_16159_simplified,)


@app.cell
def _(check_16159_simplified):
    check_16159_simplified.is_empty
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
