import marimo

__generated_with = "0.23.9"
app = marimo.App()

with app.setup:
    # Initialization code that runs before all other cells

    from typing import Callable
    import sys

    from pathlib import Path

    import numpy as np

    import mckit as mc
    from mckit import Transformation, Universe, calc_z_rotation
    from mckit.utils import map_names, check_if_path_exists, find_git_root_dir

    __version__ = "0.1.0"
    ROOT = find_git_root_dir()
    OUT = ROOT / f"wrk/demo-intersection/{__version__}"
    OUT.mkdir(parents=True, exist_ok=True)

    def make_out_path(fname: str) -> Path:
        return OUT / fname

    def print_transformation(tr: Transformation, out = sys.stdout) -> None:
        t = np.array(tr.get_words()).reshape((4,6))
        for r in t:
            print("   ", *(x.rjust(6) for x in r if x != " "), file=out)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Sector extraction demo

    Given universe construct the new one as extracted 45-degree sector.
    The sector is symmetric at XZ plane.
    """)
    return


@app.cell
def _(mo):
    mo.md(f"""
    - Python {sys.version} at {sys.prefix}
    - mckit {mc.__version__}
    - wdir: {Path.cwd()}
    - root: {ROOT}
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    universe_path = ROOT / "tests/data/universe/universe1.i"
    return (universe_path,)


@app.cell
def _(universe_path):
    universe_path.exists()
    return


@app.cell
def _(universe_path):
    universe_info = mc.from_file(universe_path)
    return (universe_info,)


@app.cell
def _(universe_info):
    universe = universe_info.universe
    return (universe,)


@app.cell
def _(universe):
    list(map_names(universe))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Compute $45^o$ sector
    """)
    return


@app.cell
def _():
    theta = 22.5
    return (theta,)


@app.cell
def _(theta):
    r_theta = calc_z_rotation(theta*np.pi/180)
    r_theta
    return (r_theta,)


@app.cell
def _(r_theta):
    tr_theta = Transformation(rotation=r_theta)
    return (tr_theta,)


@app.cell
def _(tr_theta):
    print_transformation(tr_theta)
    return


@app.cell
def _():
    from mckit import Plane
    p = Plane([0, 1, 0], 0)
    p
    return (p,)


@app.cell
def _(p, tr_theta):
    p1 = p.transform(tr_theta).apply_transformation()
    p1
    return (p1,)


@app.cell
def _(theta):
    tr_theta_complement = Transformation(rotation=calc_z_rotation(theta*np.pi/180 + np.pi))
    print_transformation(tr_theta_complement)
    return (tr_theta_complement,)


@app.cell
def _(p, tr_theta_complement):
    p1_complement = p.transform(tr_theta_complement).apply_transformation()
    p1_complement
    return (p1_complement,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ... clockwise
    """)
    return


@app.cell
def _(p, r_theta):
    p2 = p.transform(Transformation(rotation=r_theta.T)).apply_transformation()
    p2
    return (p2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Testing points: the first is in sector, the second is out.
    """)
    return


@app.cell
def _():
    points = np.array([[1, 0, 0], [-1, 0, 0]], dtype=np.float64)
    return (points,)


@app.cell
def _(p1, points):
    assert np.array_equal(p1.test_points(points), [-1,1])
    return


@app.cell
def _(p1_complement, points):
    assert np.array_equal(p1_complement.test_points(points), [1,-1])
    return


@app.cell
def _(p2, points):
    p2.test_points(points)
    return


@app.cell
def _(universe):
    from mckit.workflow import extract_cells
    grave_yard_cells = extract_cells(universe, lambda c: c.is_graveyard, add_surface_sharing_cells=False)
    return (grave_yard_cells,)


@app.cell
def _(grave_yard_cells):
    graveyard_cell_names = list(map_names(grave_yard_cells))
    assert len(graveyard_cell_names) == 1
    assert graveyard_cell_names[0] == 4
    return


@app.cell
def _(grave_yard_cells):
    scene = mc.Shape("U", *grave_yard_cells).complement()
    return (scene,)


@app.cell
def _(scene):
    scene
    return


@app.cell
def _(p1, p2):
    p1.rename(1001)
    p2.rename(1002)
    return


@app.cell
def _(p1, p2, scene):
    sector_in = mc.Shape.from_polish_notation([p1, "C", p2, "I", scene, "I"])
    return (sector_in,)


@app.cell
def _(sector_in):
    sector_in
    return


@app.cell
def _(p1, p2, scene):
    sector_out = mc.Shape.from_polish_notation([p1, p2, "C", "U", scene, "I"])
    return (sector_out,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Intersection of sector_in and sector_out is to be empty
    """)
    return


@app.cell
def _(sector_in, sector_out):
    assert mc.Body(sector_in.intersection(sector_out)).simplify()._shape.is_empty()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Union of sector_in and sector_out is to be equivalent to scene
    """)
    return


@app.cell
def _(sector_in, sector_out):
    sector_union = mc.Body(sector_out.union(sector_in))
    sector_union._shape.args
    return (sector_union,)


@app.cell
def _(sector_union):
    sector_union.simplify(min_volume=1e-5)._shape
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **TBD**

    Union simplification is not implemented yet.
    This example could be a test case. With proper implementation there should remain something like scene cell, where is the only  5-th surface.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Intersect non graveyard cells with sector
    """)
    return


@app.cell
def _(sector_in, universe):
    def _():
        return [c for c in (_c.intersection(sector_in).simplify() for _c in universe if not _c.is_graveyard) if not c._shape.is_empty()]

    new_cells = _()
    return (new_cells,)


@app.cell
def _(new_cells):
    new_cells
    return


@app.cell
def _(sector_out):
    sector_out_cell = mc.Body(sector_out, name = 1003)
    return (sector_out_cell,)


@app.cell
def _(new_cells):
    new_cells[0]._shape
    return


@app.cell
def _(new_cells):
    new_cells[1]._shape
    return


@app.cell
def _(grave_yard_cells, new_cells, sector_out_cell):
    new_universe = Universe(new_cells + [sector_out_cell] + list(grave_yard_cells)) 
    return


app._unparsable_cell(
    r"""
    new_universe.save(make_out_path(universe1+sector45.mcmp"))
    """,
    name="_"
)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
