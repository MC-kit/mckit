from __future__ import annotations

import tempfile
import textwrap

from copy import deepcopy

import numpy as np
import pytest

from mckit.body import Body, Card, Shape
from mckit.box import Box
from mckit.material import Composition, Element, Material
from mckit.parser import ParseResult, from_file, from_text
from mckit.surface import Sphere, Surface, create_surface
from mckit.transformation import Transformation
from mckit.universe import (
    NameClashError,
    Universe,
    cell_selector,
    collect_transformations,
    surface_selector,
)
from mckit.utils._resource import path_resolver

data_path_resolver = path_resolver("tests")


def data_filename_resolver(x):
    return str(data_path_resolver(x))


TStatItem = dict[int, list[int] | set[Universe]]  # TODO dvp: cool but isn't this too much freedom?
TStat = dict[str, TStatItem]


@pytest.fixture(scope="module")
def universe():
    cases = {
        1: "universe_test_data/universe1.i",
        2: "universe_test_data/universe2.i",
        3: "universe_test_data/universe3.i",
        4: "universe_test_data/universe4.i",
        5: "universe_test_data/universe5.i",
        1002: "universe_test_data/universe1002.i",
        1012: "universe_test_data/universe1012.i",
        1022: "universe_test_data/universe1022.i",
    }

    def _universe(case: int) -> Universe:
        result: ParseResult = from_file(data_filename_resolver(cases[case]))
        return result.universe

    return _universe


@pytest.mark.parametrize(
    "case, points, answer",
    [
        (
            1,
            [[-2, 0, 4], [10, 10, -10], [0, 0, 0], [0, 0, -2.5], [0, 1, 0]],
            [1, 3, 0, 2, 0],
        )
    ],
)
def test_points(universe, case, points, answer):
    u = universe(case)
    result = u.test_points(points)
    np.testing.assert_array_equal(result, answer)


_emp = Shape("R")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": 3, "verbose_name": "verbose", "comment": "comment"},
        {},
        {"name": 4, "comment": ["1", "2"]},
    ],
)
@pytest.mark.parametrize(
    "cells", [[Body(_emp, name=2), Body(_emp, name=4)], [], [Body(_emp, name=5)]]
)
def test_init(cells, kwargs):
    u = Universe(cells, **kwargs)
    assert len(u._cells) == len(cells)
    for c1, c2 in zip(u._cells, cells, strict=False):
        assert c1.name() == c2.name()
        assert c1.shape == c2.shape
    assert u.name() == kwargs.get("name", 0)
    assert u.verbose_name == kwargs.get("verbose_name", str(kwargs.get("name", 0)))
    assert u._comment == kwargs.get("comment", None)


@pytest.mark.parametrize(
    "case, cells, name_rule, new_name, new_surfs, new_comps",
    [
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=2),
            "keep",
            None,
            [],
            [],
        ),  # 0
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=2)), name=8),
            "keep",
            [8],
            None,
            [],
        ),  # 1
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=7),
            "keep",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),
        # 2
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=2),
            "clash",
            [5],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),
        # 3
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=2)), name=8),
            "clash",
            [8],
            [Sphere([0, 3, 0], 0.5, name=6)],
            [],
        ),
        # 4
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=7),
            "clash",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),
        # 5
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=2),
            "new",
            [5],
            [Sphere([0, 3, 0], 0.5, name=6)],
            [],
        ),
        # 6
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=2)), name=8),
            "new",
            [5],
            [Sphere([0, 3, 0], 0.5, name=6)],
            [],
        ),
        # 7
        (
            1,
            Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=7),
            "new",
            [5],
            [Sphere([0, 3, 0], 0.5, name=6)],
            [],
        ),
        # 8
        (
            1,
            Body(Shape("C", Sphere([0, 0, 0], 2, name=8)), name=2),
            "new",
            [5],
            [],
            [],
        ),  # 9
        (
            1,
            Body(Shape("C", Sphere([0, 0, 0], 2, name=2)), name=8),
            "keep",
            [8],
            [],
            [],
        ),  # 10
        (
            1,
            Body(Shape("C", Sphere([0, 0, 0], 2, name=8)), name=7),
            "new",
            [5],
            [],
            [],
        ),  # 11
        (
            1,
            [
                Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=8),
                Body(Shape("C", Sphere([0, 4, 0], 0.5, name=8)), name=9),
            ],
            "keep",
            [8, 9],
            None,
            [],
        ),  # 12
        (
            1,
            [
                Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=9),
                Body(Shape("C", Sphere([0, 4, 0], 0.5, name=9)), name=9),
            ],
            "keep",
            None,
            [8, 9],
            [],
        ),  # 13
        (
            1,
            [
                Body(Shape("C", Sphere([0, 3, 0], 0.5, name=2)), name=2),
                Body(Shape("C", Sphere([0, 4, 0], 0.5, name=2)), name=2),
            ],
            "clash",
            [5, 6],
            [Sphere([0, 3, 0], 0.5, name=6), Sphere([0, 4, 0], 0.5, name=7)],
            [],
        ),  # 14
        (
            1,
            [
                Body(Shape("C", Sphere([0, 3, 0], 0.5, name=8)), name=9),
                Body(Shape("C", Sphere([0, 4, 0], 0.5, name=9)), name=9),
            ],
            "new",
            [5, 6],
            [Sphere([0, 3, 0], 0.5, name=6), Sphere([0, 4, 0], 0.5, name=7)],
            [],
        ),  # 15
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(
                    composition=Composition(atomic=[("C-12", 1)], name=2, lib="31c"),
                    density=2.0,
                ),
            ),
            "keep",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),  # 16
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(
                    composition=Composition(atomic=[("C-12", 1)], name=1, lib="31c"),
                    density=2.0,
                ),
            ),
            "keep",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),  # 17
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(
                    composition=Composition(atomic=[("C-12", 1)], name=3, lib="31c"),
                    density=2.0,
                ),
            ),
            "keep",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [],
        ),  # 18
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(composition=Composition(atomic=[("Fe-56", 1)], name=2), density=2.0),
            ),
            "keep",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            None,
        ),  # 19
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(composition=Composition(atomic=[("Fe-56", 1)], name=2), density=2.0),
            ),
            "new",
            [5],
            [Sphere([0, 3, 0], 0.5, name=6)],
            [Composition(atomic=[("Fe-56", 1)], name=3)],
        ),  # 20
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(composition=Composition(atomic=[("Fe-56", 1)], name=2), density=2.0),
            ),
            "clash",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [Composition(atomic=[("Fe-56", 1)], name=3)],
        ),  # 21
        (
            1,
            Body(
                Shape("C", Sphere([0, 3, 0], 0.5, name=8)),
                name=7,
                MAT=Material(composition=Composition(atomic=[("Fe-56", 1)], name=6), density=2.0),
            ),
            "clash",
            [7],
            [Sphere([0, 3, 0], 0.5, name=8)],
            [Composition(atomic=[("Fe-56", 1)], name=6)],
        ),  # 22
    ],
)
def test_add_cells(universe, case, cells, name_rule, new_name, new_surfs, new_comps):
    u = universe(case)
    s_before = u.get_surfaces()
    c_before = u.get_compositions()
    if new_surfs is None or new_name is None or new_comps is None:
        with pytest.raises(NameClashError):
            u.add_cells(cells, name_rule=name_rule)
    else:
        u.add_cells(cells, name_rule=name_rule)
        s_after = u.get_surfaces()
        c_after = u.get_compositions()
        added_cells = u._cells[-len(new_name) :]
        if isinstance(cells, Body):
            cells = [cells]
        for added_cell, cell, name in zip(added_cells, cells, new_name, strict=False):
            assert added_cell.shape == cell.shape
            assert added_cell is not cell
            assert added_cell.name() == name
            assert added_cell.options["U"] is u
            if cell.material() is not None:
                assert added_cell.material().composition == cell.material().composition

        assert_change(s_before, s_after, new_surfs)
        assert_change(c_before, c_after, new_comps)


@pytest.mark.parametrize(
    "case, cells, shapes",
    [
        (
            1,
            Body(Shape("C", create_surface("P", 0, 0, -1, -3, name=8)), name=5),
            [Shape("S", create_surface("P", 0, 0, 1, 3, name=2))],
        )
    ],
)
def test_add_cells_neg(universe, case, cells, shapes):
    u = universe(case)
    s_before = u.get_surfaces()
    u.add_cells(cells, name_rule="keep")
    s_after = u.get_surfaces()
    if isinstance(cells, Body):
        cells = [cells]
    added_cells = u._cells[-len(cells) :]
    if isinstance(cells, Body):
        cells = [cells]
    for added_cell, cell, shape in zip(added_cells, cells, shapes, strict=False):
        assert added_cell.shape == shape
        assert added_cell is not cell
        assert added_cell.name() == cell.name()
        assert added_cell.options["U"] is u
        if cell.material() is not None:
            assert added_cell.material().composition == cell.material().composition

    assert_change(s_before, s_after, {})


@pytest.mark.parametrize(
    "case, common_materials, ans_compositions",
    [
        (
            1,
            set(),
            {
                Composition(atomic=[("C-12", 1)], name=1),
                Composition(atomic=[("H-1", 2), ("O-16", 1)], name=2, lib="31c"),
            },
        ),
        (
            1,
            {Composition(atomic=[("C-12", 1)], name=10, lib="31c")},
            {
                Composition(atomic=[("C-12", 1)], name=10, lib="31c"),
                Composition(atomic=[("H-1", 2), ("O-16", 1)], name=2, lib="31c"),
            },
        ),
        (
            1,
            {
                Composition(atomic=[("C-12", 1)], name=10, lib="31c"),
                Composition(atomic=[("H-1", 2), ("O-16", 1)], name=11, lib="31c"),
            },
            {
                Composition(atomic=[("C-12", 1)], name=10, lib="31c"),
                Composition(atomic=[("H-1", 2), ("O-16", 1)], name=11, lib="31c"),
            },
        ),
        (
            1,
            {Composition(atomic=[("Fe-56", 1)], name=10)},
            {
                Composition(atomic=[("C-12", 1)], name=1, lib="31c"),
                Composition(atomic=[("H-1", 2), ("O-16", 1)], name=2),
            },
        ),
        (1, {Composition(atomic=[("Fe-56", 1)], name=1, lib="31c")}, None),
    ],
)
def test_common_materials(universe, case, common_materials, ans_compositions):
    u = universe(case)
    if ans_compositions is None:
        with pytest.raises(NameClashError):
            Universe(u, common_materials=common_materials)
    else:
        new_u = Universe(u, common_materials=common_materials)
        new_comps = new_u.get_compositions()
        assert new_comps == ans_compositions
        common = {c.name(): c for c in common_materials}
        for c in new_comps:
            if c in common_materials:
                assert c is common[c.name()]


def assert_change(before, after, new_items):
    for s in before:
        assert s in after
    assert len(after) - len(before) == len(new_items)
    diff = after.difference(before)
    assert diff == set(new_items)
    assert {s.name() for s in diff} == {s.name() for s in new_items}


@pytest.mark.parametrize(
    "case, recursive, answer_data",
    [
        (
            1,
            False,
            [
                (1, "SO", [2]),
                (2, "PZ", [3]),
                (3, "PZ", [5]),
                (4, "C/Z", [-2, 0, 1]),
                (5, "SZ", [3.5, 10]),
            ],
        ),
        (
            1,
            True,
            [
                (1, "SO", [2]),
                (2, "PZ", [3]),
                (3, "PZ", [5]),
                (4, "C/Z", [-2, 0, 1]),
                (5, "SZ", [3.5, 10]),
            ],
        ),
    ],
)
def test_get_surfaces(universe, case, recursive, answer_data):
    answer = {create_surface(k, *p, name=n) for n, k, p in answer_data}
    u = universe(case)
    surfaces = u.get_surfaces(inner=recursive)
    assert surfaces == answer
    names_ans = {x[0] for x in answer_data}
    names = {s.name() for s in surfaces}
    assert names == names_ans


@pytest.mark.parametrize(
    "case, answer", [(5, {Composition(atomic=[("6012", 1)], name=10)}), (1, set())]
)
def test_find_common_materials(universe, case, answer):
    u = universe(case)
    cm = u._common_materials
    assert cm == answer
    assert {c.name() for c in cm} == {c.name() for c in answer}


@pytest.mark.parametrize(
    "case, answer",
    [
        (
            1,
            {
                Composition(atomic=[(Element("C-12", lib="31c"), 1)], name=1),
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                ),
            },
        ),
        (2, set()),
        (
            3,
            {
                Composition(atomic=[(Element("C-12", lib="31c"), 1)], name=4),
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=3,
                ),
            },
        ),
    ],
)
def test_get_compositions(universe, case, answer):
    u = universe(case)
    comps = u.get_compositions()
    assert comps == answer
    names_ans = {c.name() for c in answer}
    names = {c.name() for c in comps}
    assert names == names_ans


@pytest.mark.parametrize(
    "tr",
    [
        Transformation(translation=[-3, 2, 0.5]),
        Transformation(translation=[1, 2, 3]),
        Transformation(translation=[-4, 2, -3]),
        Transformation(
            translation=[3, 0, 9],
            rotation=[30, 60, 90, 120, 30, 90, 90, 90, 0],
            indegrees=True,
        ),
        Transformation(
            translation=[1, 4, -2],
            rotation=[0, 90, 90, 90, 30, 60, 90, 120, 30],
            indegrees=True,
        ),
        Transformation(
            translation=[-2, 5, 3],
            rotation=[30, 90, 60, 90, 0, 90, 120, 90, 30],
            indegrees=True,
        ),
    ],
)
@pytest.mark.parametrize("case, extent", [(1, [20, 10, 10])])
def test_transform(universe, case, tr, extent):
    u = universe(case)
    points = np.random.default_rng().random((50000, 3))
    points -= np.array([0.5, 0.5, 0.5])
    points *= np.array(extent)
    test_results = [c.shape.test_points(points) for c in u]

    tr_u = u.transform(tr)
    tr_points = tr.apply2point(points)
    tr_results = [c.shape.test_points(tr_points) for c in tr_u]
    assert len(u._cells) == len(tr_u._cells)
    for r, r_tr in zip(test_results, tr_results, strict=False):
        np.testing.assert_array_equal(r, r_tr)


@pytest.mark.parametrize("case", [1])
def test_copy(universe, case):
    u = universe(case)
    uc = u.copy()
    assert uc is not u
    assert u.name() == uc.name()
    assert u.verbose_name == uc.verbose_name
    assert u._comment == uc._comment
    assert len(u._cells) == len(uc._cells)
    for c, cc in zip(u, uc, strict=False):
        assert cc is not c
        assert c.name() == cc.name()
        assert c.shape == cc.shape
    surfaces_idx = {s.name(): s for s in u.get_surfaces()}
    copy_surfaces_idx = {s.name(): s for s in uc.get_surfaces()}
    assert surfaces_idx == copy_surfaces_idx
    for k, v in surfaces_idx.items():
        assert copy_surfaces_idx[k] is not v
        assert copy_surfaces_idx[k] == v


@pytest.mark.slow
@pytest.mark.parametrize("tol", [0.2, None])
@pytest.mark.parametrize("case, expected", [(1, [[-10, 10], [-10, 10], [-6.5, 13.5]])])
def test_bounding_box(universe, tol, case, expected):
    u = universe(case)
    base = [0, 0, 0]
    dims = [30, 30, 30]
    gb = Box(base, dims[0], dims[1], dims[2])
    if tol is not None:
        bb = u.bounding_box(box=gb, tol=tol)
    else:
        tol = 100.0
        bb = u.bounding_box()
    for j, (low, high) in enumerate(expected):
        dimensions = 0.5 * bb.dimensions[j]
        assert bb.center[j] - dimensions <= low
        assert bb.center[j] - dimensions >= low - tol
        assert bb.center[j] + dimensions >= high
        assert bb.center[j] + dimensions <= high + tol


@pytest.mark.parametrize(
    "case, condition, inner, answer",
    [
        (1, cell_selector(1), False, [(Body, 1)]),
        (1, cell_selector([1, 3]), False, [(Body, 1), (Body, 3)]),
        (1, surface_selector(1), False, [(Surface, 1)]),
        (1, surface_selector([1, 4]), False, [(Surface, 1), (Surface, 4)]),
        (1, lambda c: [c] if c.material() else [], False, [(Body, 1), (Body, 2)]),
        (2, cell_selector(3), False, [(Body, 3)]),
        (2, cell_selector(11), False, []),
        (2, cell_selector(11), True, [(Body, 11)]),
    ],
)
def test_select(universe, case, condition, inner, answer):
    u = universe(case)
    selection = u.select(condition, inner=inner)
    assert len(selection) == len(answer)
    for r, (cls, name) in zip(selection, answer, strict=False):
        assert isinstance(r, cls)
        assert r.name() == name


@pytest.mark.parametrize(
    "case, answer",
    [(1, {0: {1, 2, 3, 4}}), (2, {0: {1, 2, 3}, 1: {10, 11, 12}, 2: {21, 22, 23, 24}})],
)
def test_get_universes(universe, case, answer):
    u = universe(case)
    universes = u.get_universes()
    assert len(universes) == len(answer.keys())
    named_u = {x.name(): x for x in universes}
    for k, v in named_u.items():
        names = {c.name() for c in v}
        assert names == answer[k]


@pytest.mark.parametrize(
    "case, rename, stat",
    [
        (1, {}, {}),
        (2, {}, {}),
        (2, {2: {"start_cell": 2}}, {"cell": {2: [0, 2], 3: [0, 2]}}),
        (2, {2: {"start_surf": 2}}, {"surf": {2: [0, 2], 3: [0, 2], 4: [0, 2]}}),
        (
            2,
            {2: {"start_cell": 2, "start_surf": 3}},
            {"cell": {2: [0, 2], 3: [0, 2]}, "surf": {3: [0, 2], 4: [0, 2]}},
        ),
        (
            2,
            {2: {"start_cell": 2}, 1: {"start_cell": 1}},
            {"cell": {1: [0, 1], 2: [0, 1, 2], 3: [0, 1, 2]}},
        ),
        (2, {1: {"name": 2}}, {"universe": {2: [1, 2]}}),
        (2, {1: {"name": 3}, 2: {"name": 3}}, {"universe": {3: [1, 2]}}),
        (2, {1: {"start_mat": 19}}, {}),
        (2, {1: {"start_mat": 20}}, {"material": {21: [1, 2]}}),
        (2, {1: {"start_mat": 21}}, {"material": {21: [1, 2], 22: [1, 2]}}),
        (
            2,
            {1: {"start_mat": 20}, 2: {"start_cell": 2}},
            {"material": {21: [1, 2]}, "cell": {2: [0, 2], 3: [0, 2]}},
        ),
        (
            2,
            {1: {"start_mat": 21}, 2: {"start_cell": 2}},
            {"material": {21: [1, 2], 22: [1, 2]}, "cell": {2: [0, 2], 3: [0, 2]}},
        ),
        (3, {}, {}),
        (4, {}, {}),
    ],
)
def test_name_clashes(
    universe,
    case: int,
    rename: dict[int, dict[str, int]],
    stat: TStat,
):
    rename = deepcopy(rename)
    stat = deepcopy(stat)
    u: Universe = universe(case)
    universes_index: dict[int, Universe] = {x.name(): x for x in u.get_universes()}
    for uname, ren_dict in rename.items():
        universes_index[uname].rename(**ren_dict)
    for stat_item in stat.values():
        for kind, universe_names in stat_item.items():
            stat_item[kind] = {universes_index[uname] for uname in universe_names}
    s = u.name_clashes()
    assert s == stat


@pytest.mark.parametrize(
    "case, common_mat, stat",
    [
        (2, {Composition(atomic=[("6012", 1)], name=1)}, {}),
        (2, {Composition(atomic=[("6012", 1)], name=10)}, {}),
        (
            2,
            {Composition(atomic=[("7014", 1)], name=10)},
            {"material": {10: [1, None]}},
        ),
        (
            2,
            {
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                )
            },
            {},
        ),
        (
            2,
            {
                Composition(
                    atomic=[
                        (Element("H2", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=11,
                )
            },
            {"material": {11: [1, None]}},
        ),
        (
            2,
            {
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=21,
                )
            },
            {"material": {21: [2, None]}},
        ),
        (
            2,
            {
                Composition(atomic=[("7012", 1)], name=10),
                Composition(
                    atomic=[
                        (Element("H2", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=11,
                ),
            },
            {"material": {10: [1, None], 11: [1, None]}},
        ),
    ],
)
def test_name_clashes_with_common_materials(
    universe,
    case: int,
    common_mat: set[Composition],
    stat: TStat,
):
    stat = deepcopy(stat)
    u = universe(case)
    universes_idx = {x.name(): x for x in u.get_universes()}
    u.set_common_materials(common_mat)
    for stat_item in stat.values():
        for kind, universes_names in stat_item.items():
            stat_item[kind] = {universes_idx[uname] if uname else None for uname in universes_names}
    s = u.name_clashes()
    assert s == stat


@pytest.mark.parametrize(
    "case, common_mat",
    [
        (2, {Composition(atomic=[("6012", 1)], name=1)}),
        (
            2,
            {
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                )
            },
        ),
        (
            2,
            {
                Composition(atomic=[("6012", 1)], name=1),
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                ),
            },
        ),
        (2, {Composition(atomic=[("Li", 1)], name=3)}),
    ],
)
def test_set_common_materials(universe, case, common_mat):
    u = universe(case)
    universes = u.get_universes()
    mats_before = {un: un.get_compositions() for un in universes}
    u.set_common_materials(common_mat)
    cm = {c: c for c in common_mat}
    for un in universes:
        assert mats_before[un] == un.get_compositions()
        for c in un:
            mat = c.material()
            if mat:
                comp = mat.composition
                if comp in common_mat:
                    assert comp is cm[comp]


@pytest.mark.slow
@pytest.mark.parametrize(
    "case, condition, answer_case, box",
    [
        (2, {}, 1002, Box([0, 0, 0], 20, 20, 20)),
        (2, {"cell": 1}, 1012, Box([0, 0, 0], 20, 20, 20)),
        (2, {"cell": 2}, 1022, Box([0, 0, 0], 20, 20, 20)),
        (2, {"universe": 1}, 1022, Box([0, 0, 0], 20, 20, 20)),
        (2, {"universe": 2}, 1012, Box([0, 0, 0], 20, 20, 20)),
        (
            2,
            {"predicate": lambda c: "transform" in c.options["FILL"]},
            1022,
            Box([0, 0, 0], 20, 20, 20),
        ),
    ],
)
def test_apply_fill(universe, case, condition, answer_case, box):
    u = universe(case)
    ua = universe(answer_case)
    u.apply_fill(**condition)
    points = box.generate_random_points(1000000)
    test_f = u.test_points(points)
    test_a = ua.test_points(points)
    np.testing.assert_array_equal(test_f, test_a)


@pytest.mark.parametrize(
    "case, start, answer",
    [
        (
            1,
            {"name": 4},
            {
                "name": 4,
                "cell": [1, 2, 3, 4],
                "surface": [1, 2, 3, 4, 5],
                "material": [1, 2],
            },
        ),
        (
            1,
            {"start_cell": 6},
            {
                "name": 0,
                "cell": [6, 7, 8, 9],
                "surface": [1, 2, 3, 4, 5],
                "material": [1, 2],
            },
        ),
        (
            1,
            {"start_surf": 7},
            {
                "name": 0,
                "cell": [1, 2, 3, 4],
                "surface": [7, 8, 9, 10, 11],
                "material": [1, 2],
            },
        ),
        (
            1,
            {"name": 4, "start_cell": 6, "start_surf": 7},
            {
                "name": 4,
                "cell": [6, 7, 8, 9],
                "surface": [7, 8, 9, 10, 11],
                "material": [1, 2],
            },
        ),
        (
            1,
            {"name": 4, "start_mat": 5},
            {
                "name": 4,
                "cell": [1, 2, 3, 4],
                "surface": [1, 2, 3, 4, 5],
                "material": [5, 6],
            },
        ),
        (
            1,
            {"start_cell": 6, "start_mat": 6},
            {
                "name": 0,
                "cell": [6, 7, 8, 9],
                "surface": [1, 2, 3, 4, 5],
                "material": [6, 7],
            },
        ),
        (
            1,
            {"start_surf": 7, "start_mat": 4},
            {
                "name": 0,
                "cell": [1, 2, 3, 4],
                "surface": [7, 8, 9, 10, 11],
                "material": [4, 5],
            },
        ),
        (
            1,
            {"name": 4, "start_cell": 6, "start_surf": 7, "start_mat": 4},
            {
                "name": 4,
                "cell": [6, 7, 8, 9],
                "surface": [7, 8, 9, 10, 11],
                "material": [4, 5],
            },
        ),
    ],
)
def test_rename(universe, case, start, answer):
    u = universe(case)
    u.rename(**start)
    assert u.name() == answer["name"]
    cell_names = sorted(c.name() for c in u)
    surface_names = sorted(s.name() for s in u.get_surfaces())
    composition_names = sorted(m.name() for m in u.get_compositions())
    assert cell_names == answer["cell"]
    assert surface_names == answer["surface"]
    assert composition_names == answer["material"]


@pytest.mark.parametrize("case", [1, 2])
def test_alone(universe, case):
    u = universe(case)
    current_universe = u.alone()
    assert current_universe is not u
    assert current_universe.name() == 0
    assert u.verbose_name == current_universe.verbose_name
    assert len(u._cells) == len(current_universe._cells)
    for c, cc in zip(u, current_universe, strict=False):
        assert cc is not c
        assert c.name() == cc.name()
        assert c.shape == cc.shape
        assert "FILL" not in cc.options
    surfs = {s.name(): s for s in u.get_surfaces()}
    current_universe_surfs = {s.name(): s for s in current_universe.get_surfaces()}
    assert surfs == current_universe_surfs
    for k, v in surfs.items():
        assert current_universe_surfs[k] is not v
        assert current_universe_surfs[k] == v


@pytest.mark.parametrize(
    "case, common, start, answer",
    [
        (1, set(), 7, [7, 8]),
        (1, {Composition(atomic=[("C-12", 1)], name=1)}, 7, [1, 7]),
        (
            1,
            {
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                )
            },
            7,
            [2, 7],
        ),
        (
            1,
            {
                Composition(atomic=[("C-12", 1)], name=1),
                Composition(
                    atomic=[
                        (Element("H1", lib="31c"), 2 / 3),
                        (Element("O16", lib="31c"), 1 / 3),
                    ],
                    name=2,
                ),
            },
            7,
            [1, 2],
        ),
    ],
)
def test_rename_when_common_mat(universe, case, common, start, answer):
    u = Universe(universe(case), common_materials=common)
    u.rename(start_mat=start)
    composition_names = sorted(m.name() for m in u.get_compositions())
    assert composition_names == answer


@pytest.mark.slow
@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize(
    "case, complexities", [(1, {1: 1, 2: 3, 3: 5, 4: 1}), (3, {1: 1, 2: 3, 4: 5, 5: 1})]
)
def test_simplify(universe, case, complexities, verbose):
    u = universe(case)
    u.simplify(min_volume=0.1, verbose=verbose)
    assert len(u._cells) == len(complexities.keys())
    for c in u:
        assert c.shape.complexity() == complexities[c.name()]


@pytest.mark.parametrize(
    "case, box",
    [
        (1, Box([0, 0, 0], 20, 20, 20)),
        (2, Box([0, 0, 0], 20, 20, 20)),
        (3, Box([0, 0, 0], 20, 20, 20)),
    ],
)
def test_save(universe, case, box):
    u = universe(case)
    out = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    u.save(out.name)
    out.close()
    ur = from_file(out.name).universe

    points = box.generate_random_points(100000)
    universes_orig = {x.name(): x for x in u.get_universes()}
    universes_expected = {x.name(): x for x in ur.get_universes()}
    assert universes_orig.keys() == universes_expected.keys()
    for k, univ in universes_orig.items():
        test_a = univ.test_points(points)
        test_f = universes_expected[k].test_points(points)
        np.testing.assert_array_equal(test_f, test_a)


@pytest.mark.parametrize(
    "case, rename",
    [
        (2, {2: {"start_cell": 2}}),
        (2, {2: {"start_surf": 2}}),
        (2, {2: {"start_cell": 2, "start_surf": 3}}),
        (2, {2: {"start_cell": 2}, 1: {"start_cell": 1}}),
    ],
)
def test_save_exception(tmp_path, universe, case, rename):
    u = universe(case)
    universes_idx = {x.name(): x for x in u.get_universes()}
    for uname, ren_dict in rename.items():
        universes_idx[uname].rename(**ren_dict)
    with pytest.raises(NameClashError):
        u.save(tmp_path / f"{case}.i")


@pytest.mark.parametrize(
    "case, rename",
    [
        (2, {1: {"name": 2}}),
        (2, {1: {"name": 3}, 2: {"name": 3}}),
    ],
)
def test_save_exception2(tmp_path, universe, case, rename):
    u = universe(case)
    universes_idx = {x.name(): x for x in u.get_universes()}
    for uname, ren_dict in rename.items():
        universes_idx[uname].rename(**ren_dict)
    with pytest.raises(NameClashError):
        u.save(tmp_path / f"{case}.i", check_clashes=True)


@pytest.mark.parametrize(
    "case, expected",
    [
        (
            """\
                0
                1 0 -1
                2 0  1

                1 1 so 1

                TR1 1 1 1
            """,
            [],
        ),
        (
            """\
            0
            1 0 -1
            2 0  1

            1 1 so 1

            TR1 1 1 1
            """,
            [],
        ),
        (
            """\
            0
            1 0 -1 -2
            2 0  1

            1 1 so 2
            2 2 so 3

            TR1 1 1 1
            TR2 -1 -1 -1
            """,
            [],
        ),
        (
            """\
            0
            1 0 -1 -2
            2 0  1 fill=1 (3) $ fill with named transformation
            3 0  3 u=1

            1 1 so 2
            2 2 so 3
            3 so 4

            TR1 1 1 1
            TR2 -1 -1 -1
            TR3  0 1 0
            """,
            [3],
        ),
    ],
)
def test_collect_transformations(case: str, expected: list[int]) -> None:
    """Only transformations to filling universes should remain in the model."""
    case = textwrap.dedent(case)
    u = from_text(case).universe
    actual = sorted(map(int, map(Card.name, collect_transformations(u))))
    assert actual == expected
