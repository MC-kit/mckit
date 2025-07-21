from __future__ import annotations

from typing import Final

import numpy as np
import pytest

from mckit.box import Box
from mckit.surface import BOX, RCC, Cone, Cylinder, GQuadratic, Plane, Sphere, Torus, create_surface
from mckit.transformation import Transformation

from tests import pass_through_pickle


@pytest.fixture(
    scope="module",
    params=[
        {},
        {
            "translation": [1, 2, -3],
            "indegrees": True,
            "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
        },
    ],
)
def transform(request):
    return Transformation(**request.param)


@pytest.fixture(scope="module")
def box():
    return Box([0, 0, 0], 2, 2, 2)


def assert_mcnp_repr(desc, answer):
    if "\n" in desc:
        assert desc.split() == answer.split()
    else:
        assert desc == answer


@pytest.mark.parametrize(
    "cls, kind, params, expected",
    [
        (Plane, "PX", [5.3], {"_v": [1, 0, 0], "_k": -5.3}),  # 0
        (Plane, "PY", [5.4], {"_v": [0, 1, 0], "_k": -5.4}),  # 1
        (Plane, "PZ", [5.5], {"_v": [0, 0, 1], "_k": -5.5}),
        (
            Plane,
            "P",
            [3.2, -1.4, 5.7, -4.8],
            {"_v": [0.47867947, -0.20942227, 0.8526478], "_k": 0.7180192041541256},
        ),
        (Plane, "X", [5.6, 6.7], {"_v": [1, 0, 0], "_k": -5.6}),
        (Plane, "Y", [5.7, 6.8], {"_v": [0, 1, 0], "_k": -5.7}),
        (Plane, "Z", [5.8, -6.9], {"_v": [0, 0, 1], "_k": -5.8}),
        (Plane, "X", [5.6, 6.7, 5.6, -7.9], {"_v": [1, 0, 0], "_k": -5.6}),
        (Plane, "Y", [5.7, 6.8, 5.7, 6.2], {"_v": [0, 1, 0], "_k": -5.7}),
        (Plane, "Z", [5.8, -6.9, 5.8, -9.9], {"_v": [0, 0, 1], "_k": -5.8}),
        (Sphere, "SO", [6.1], {"_center": [0, 0, 0], "_radius": 6.1}),
        (Sphere, "SX", [-3.4, 6.2], {"_center": [-3.4, 0, 0], "_radius": 6.2}),  # 10
        (Sphere, "SY", [3.5, 6.3], {"_center": [0, 3.5, 0], "_radius": 6.3}),
        (Sphere, "SZ", [-3.6, 6.4], {"_center": [0, 0, -3.6], "_radius": 6.4}),
        (
            Sphere,
            "S",
            [3.7, -3.8, 3.9, 6.5],
            {"_center": [3.7, -3.8, 3.9], "_radius": 6.5},
        ),
        (Cylinder, "CX", [6.6], {"_pt": [0, 0, 0], "_axis": [1, 0, 0], "_radius": 6.6}),
        (Cylinder, "CY", [6.7], {"_pt": [0, 0, 0], "_axis": [0, 1, 0], "_radius": 6.7}),
        (Cylinder, "CZ", [6.8], {"_pt": [0, 0, 0], "_axis": [0, 0, 1], "_radius": 6.8}),
        (
            Cylinder,
            "C/X",
            [4.0, -4.1, 6.9],
            {"_pt": [0, 4.0, -4.1], "_axis": [1, 0, 0], "_radius": 6.9},
        ),
        (
            Cylinder,
            "C/Y",
            [-4.2, 4.3, 7.0],
            {"_pt": [-4.2, 0, 4.3], "_axis": [0, 1, 0], "_radius": 7.0},
        ),
        (
            Cylinder,
            "C/Z",
            [4.4, 4.5, 7.1],
            {"_pt": [4.4, 4.5, 0], "_axis": [0, 0, 1], "_radius": 7.1},
        ),
        (
            Cylinder,
            "X",
            [1.2, 3.4, 8.4, 3.4],
            {"_pt": [0, 0, 0], "_axis": [1, 0, 0], "_radius": 3.4},
        ),  # 20
        (
            Cylinder,
            "Y",
            [1.2, 3.4, 8.4, 3.4],
            {"_pt": [0, 0, 0], "_axis": [0, 1, 0], "_radius": 3.4},
        ),
        (
            Cylinder,
            "Z",
            [1.2, 3.4, 8.4, 3.4],
            {"_pt": [0, 0, 0], "_axis": [0, 0, 1], "_radius": 3.4},
        ),
        (
            Cone,
            "KX",
            [4.6, 0.33],
            {"_apex": [4.6, 0, 0], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "KY",
            [4.7, 0.33],
            {"_apex": [0, 4.7, 0], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "KZ",
            [-4.8, 0.33],
            {"_apex": [0, 0, -4.8], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "K/X",
            [4.9, -5.0, 5.1, 0.33],
            {"_apex": [4.9, -5.0, 5.1], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "K/Y",
            [-5.0, -5.1, 5.2, 0.33],
            {"_apex": [-5.0, -5.1, 5.2], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "K/Z",
            [5.3, 5.4, 5.5, 0.33],
            {"_apex": [5.3, 5.4, 5.5], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": 0},
        ),
        (
            Cone,
            "KX",
            [4.6, 0.33, +1],
            {"_apex": [4.6, 0, 0], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": +1},
        ),
        (
            Cone,
            "KY",
            [4.7, 0.33, +1],
            {"_apex": [0, 4.7, 0], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": +1},
        ),  # 30
        (
            Cone,
            "KZ",
            [-4.8, 0.33, +1],
            {"_apex": [0, 0, -4.8], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": +1},
        ),
        (
            Cone,
            "X",
            [-1.0, 1.0, 1.0, 2.0],
            {"_apex": [-3.0, 0, 0], "_axis": [1, 0, 0], "_t2": 0.25, "_sheet": +1},
        ),
        (
            Cone,
            "X",
            [-2.5, 4.5, -0.5, 3.5],
            {"_apex": [6.5, 0, 0], "_axis": [1, 0, 0], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "X",
            [1.0, 2.0, -1.0, 1.0],
            {"_apex": [-3.0, 0, 0], "_axis": [1, 0, 0], "_t2": 0.25, "_sheet": +1},
        ),
        (
            Cone,
            "X",
            [-0.5, 3.5, -2.5, 4.5],
            {"_apex": [6.5, 0, 0], "_axis": [1, 0, 0], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "Y",
            [-1.0, 1.0, 1.0, 2.0],
            {"_apex": [0, -3.0, 0], "_axis": [0, 1, 0], "_t2": 0.25, "_sheet": +1},
        ),
        (
            Cone,
            "Y",
            [-2.5, 4.5, -0.5, 3.5],
            {"_apex": [0, 6.5, 0], "_axis": [0, 1, 0], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "Y",
            [1.0, 2.0, -1.0, 1.0],
            {"_apex": [0, -3.0, 0], "_axis": [0, 1, 0], "_t2": 0.25, "_sheet": +1},
        ),
        (
            Cone,
            "Y",
            [-0.5, 3.5, -2.5, 4.5],
            {"_apex": [0, 6.5, 0], "_axis": [0, 1, 0], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "Z",
            [-1.0, 1.0, 1.0, 2.0],
            {"_apex": [0, 0, -3.0], "_axis": [0, 0, 1], "_t2": 0.25, "_sheet": +1},
        ),  # 40
        (
            Cone,
            "Z",
            [-2.5, 4.5, -0.5, 3.5],
            {"_apex": [0, 0, 6.5], "_axis": [0, 0, 1], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "Z",
            [1.0, 2.0, -1.0, 1.0],
            {"_apex": [0, 0, -3.0], "_axis": [0, 0, 1], "_t2": 0.25, "_sheet": +1},
        ),
        (
            Cone,
            "Z",
            [-0.5, 3.5, -2.5, 4.5],
            {"_apex": [0, 0, 6.5], "_axis": [0, 0, 1], "_t2": 0.25, "_sheet": -1},
        ),
        (
            Cone,
            "K/X",
            [4.9, -5.0, 5.1, 0.33, +1],
            {"_apex": [4.9, -5.0, 5.1], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": +1},
        ),
        (
            Cone,
            "K/Y",
            [-5.0, -5.1, 5.2, 0.33, +1],
            {"_apex": [-5.0, -5.1, 5.2], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": +1},
        ),
        (
            Cone,
            "K/Z",
            [5.3, 5.4, 5.5, 0.33, +1],
            {"_apex": [5.3, 5.4, 5.5], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": +1},
        ),
        (
            Cone,
            "KX",
            [4.6, 0.33, -1],
            {"_apex": [4.6, 0, 0], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": -1},
        ),
        (
            Cone,
            "KY",
            [4.7, 0.33, -1],
            {"_apex": [0, 4.7, 0], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": -1},
        ),
        (
            Cone,
            "KZ",
            [-4.8, 0.33, -1],
            {"_apex": [0, 0, -4.8], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": -1},
        ),
        (
            Cone,
            "K/X",
            [4.9, -5.0, 5.1, 0.33, -1],
            {"_apex": [4.9, -5.0, 5.1], "_axis": [1, 0, 0], "_t2": 0.33, "_sheet": -1},
        ),  # 50
        (
            Cone,
            "K/Y",
            [-5.0, -5.1, 5.2, 0.33, -1],
            {"_apex": [-5.0, -5.1, 5.2], "_axis": [0, 1, 0], "_t2": 0.33, "_sheet": -1},
        ),
        (
            Cone,
            "K/Z",
            [5.3, 5.4, 5.5, 0.33, -1],
            {"_apex": [5.3, 5.4, 5.5], "_axis": [0, 0, 1], "_t2": 0.33, "_sheet": -1},
        ),
        (
            Torus,
            "TX",
            [1, 2, -3, 5, 0.5, 0.8],
            {"_center": [1, 2, -3], "_axis": [1, 0, 0], "_R": 5, "_a": 0.5, "_b": 0.8},
        ),
        (
            Torus,
            "TY",
            [-4, 5, -6, 3, 0.9, 0.2],
            {"_center": [-4, 5, -6], "_axis": [0, 1, 0], "_R": 3, "_a": 0.9, "_b": 0.2},
        ),
        (
            Torus,
            "TZ",
            [0, -3, 5, 1, 0.1, 0.2],
            {"_center": [0, -3, 5], "_axis": [0, 0, 1], "_R": 1, "_a": 0.1, "_b": 0.2},
        ),
        (
            GQuadratic,
            "SQ",
            [0.5, -2.5, 3.0, 1.1, -1.3, -5.4, -7.0, 3.2, -1.7, 8.4],
            {
                "_m": np.diag([0.5, -2.5, 3.0]),
                "_v": 2 * np.array([1.1 - 0.5 * 3.2, -1.3 - 2.5 * 1.7, -5.4 - 3.0 * 8.4]),
                "_k": 0.5 * 3.2**2
                - 2.5 * 1.7**2
                + 3.0 * 8.4**2
                - 7.0
                - 2 * (1.1 * 3.2 + 1.3 * 1.7 - 5.4 * 8.4),
            },
        ),
        (
            GQuadratic,
            "GQ",
            [1, 2, 3, 4, 5, 6, 7, 8, 9, -10],
            {"_m": [[1, 2, 3], [2, 2, 2.5], [3, 2.5, 3]], "_v": [7, 8, 9], "_k": -10},
        ),
    ],
)
def test_surface_creation(cls, kind, params, expected):
    surf = create_surface(kind, *params)
    assert isinstance(surf, cls)
    for attr_name, attr_value in expected.items():
        surf_attr = getattr(surf, attr_name)
        np.testing.assert_array_almost_equal(surf_attr, attr_value)


@pytest.mark.parametrize(
    "tr",
    [
        None,
        Transformation([0, 0, 0], [20.0, 70.0, 90, 110.0, 20.0, 90, 90, 90, 0], indegrees=True),
    ],
)
@pytest.mark.parametrize(
    "cls, kind, params",
    [
        (Plane, "P", [3.2, -1.4, 5.7, -4.8]),
        (Plane, "P", [3.28434343457632, -1.48888888888888, 5.7341411411414, -4.8]),
        (
            Plane,
            "P",
            [
                -0.176628496439844,
                -0.005226281717615,
                0.984263714776080,
                342.264078203542790,
            ],
        ),
        (Sphere, "S", [3.7, -3.8, 3.9, 6.5]),
        (Cylinder, "CX", [6.6]),
        (Cylinder, "CY", [6.7]),
        (Cylinder, "CZ", [6.8]),
        (Cylinder, "C/X", [4.0, -4.1, 6.9]),
        (Cylinder, "C/Y", [-4.2, 4.3, 7.0]),
        (Cylinder, "C/Z", [4.4, 4.5, 7.1]),
        (Cylinder, "C/X", [72.4, 157.0, 25.5]),
        (Cylinder, "X", [1.2, 3.4, 8.4, 3.4]),
        (Cylinder, "Y", [1.2, 3.4, 8.4, 3.4]),
        (Cylinder, "Z", [1.2, 3.4, 8.4, 3.4]),
        (Cone, "KX", [4.6, 0.33]),
        (Cone, "KY", [4.7, 0.33]),
        (Cone, "KX", [4.77777777777777777, 0.333333333333333]),
        (Cone, "KZ", [-4.8, 0.33]),
        (Cone, "K/X", [4.9, -5.0, 5.1, 0.33]),
        (Cone, "K/Y", [-5.0, -5.1, 5.2, 0.33]),
        (Cone, "K/Z", [5.3, 5.4, 5.5, 0.33]),
        (Cone, "KX", [4.6, 0.33, +1]),
        (Cone, "KY", [4.7, 0.33, +1]),
        (Cone, "KZ", [-4.8, 0.33, +1]),
        (Cone, "X", [-1.0, 1.0, 1.0, 2.0]),
        (Cone, "X", [-2.5, 4.5, -0.5, 3.5]),
        (Cone, "X", [1.0, 2.0, -1.0, 1.0]),
        (Cone, "X", [-0.5, 3.5, -2.5, 4.5]),
        (Cone, "Y", [-1.0, 1.0, 1.0, 2.0]),
        (Cone, "Y", [-2.5, 4.5, -0.5, 3.5]),
        (Cone, "Y", [1.0, 2.0, -1.0, 1.0]),
        (Cone, "Y", [-0.52222989232331345, 3.5, -2.5, 4.5]),
        (Cone, "Z", [-1.0, 1.0, 1.0, 2.0]),
        (Cone, "Z", [-2.5, 4.5, -0.5, 3.5]),
        (Cone, "Z", [1.0, 2.0, -1.0, 1.0]),
        (Cone, "Z", [-0.5, 3.5, -2.5, 4.5]),
        (Cone, "K/X", [4.9, -5.0, 5.1, 0.33, +1]),
        (Cone, "K/Y", [-5.0, -5.1, 5.2, 0.33, +1]),
        (Cone, "K/Z", [5.3, 5.4, 5.5, 0.33, +1]),
        (Cone, "KX", [4.6, 0.33, -1]),
        (Cone, "KY", [4.7, 0.33, -1]),
        (Cone, "KZ", [-4.8, 0.33, -1]),
        (Cone, "K/X", [4.9, -5.0, 5.1, 0.33, -1]),
        (Cone, "K/Y", [-5.0, -5.1, 5.2, 0.33, -1]),
        (Cone, "K/Z", [5.3, 5.4, 5.5, 0.33, -1]),
        (Torus, "TX", [1, 2, -3, 5, 0.5, 0.8]),
        (Torus, "TY", [-4, 5, -6, 3, 0.9, 0.2]),
        (Torus, "TZ", [0, -3, 5, 1, 0.1, 0.2]),
        (
            GQuadratic,
            "SQ",
            [0.5, -2.5841834141234512351, 3.0, 1.1, -1.3, -5.4, -7.0, 3.2, -1.7, 8.4],
        ),
        (GQuadratic, "GQ", [1, 2, 3, 4, 5, 6, 7, 8, 9, -10]),
    ],
)
def test_surface_copy(cls, kind, params, tr):
    options = {"transform": tr} if tr else {}
    surf = create_surface(kind, *params, **options)
    surf_cpy = surf.copy()
    assert id(surf) != id(surf_cpy)
    assert isinstance(surf_cpy, surf.__class__)
    assert surf == surf_cpy


@pytest.mark.parametrize(
    "kind, params, name",
    [("PX", [1], 2), ("CX", [1], 3), ("SO", [1], 4), ("KX", [1, 2], 5)],
)
def test_surface_name(kind, params, name):
    surf = create_surface(kind, *params, name=name)
    assert surf.name() == name


class TestPlane:
    @pytest.mark.parametrize(
        "norm, offset, v, k",
        [
            ([0, 0, 1], -2, np.array([0, 0, 1]), -2),
            ([1, 0, 0], -2, np.array([1, 0, 0]), -2),
            ([0, 1, 0], -2, np.array([0, 1, 0]), -2),
        ],
    )
    def test_init(self, transform, norm, offset, v, k):
        surf = Plane(norm, offset, transform=transform)
        surf = surf.apply_transformation()
        v, k = transform.apply2plane(v, k)
        np.testing.assert_array_almost_equal(v, surf._v)
        np.testing.assert_array_almost_equal(k, surf._k)

    @pytest.mark.parametrize(
        "point, expected",
        [
            ([1, 0, 0], [+1]),
            ([-1, 0, 0], [-1]),
            ([0.1, 0, 0], [+1]),
            ([-0.1, 0, 0], [-1]),
            ([1.0e-6, 100, -300], [+1]),
            ([-1.0e-6, 200, -500], [-1]),
            (
                np.array(
                    [
                        [1, 0, 0],
                        [-1, 0, 0],
                        [0.1, 0, 0],
                        [-0.1, 0, 0],
                        [1.0e-6, 100, -300],
                        [-1.0e-6, 200, -500],
                    ]
                ),
                np.array([1, -1, 1, -1, 1, -1]),
            ),
        ],
    )
    def test_point_test(self, point, expected):
        surf = Plane([1, 0, 0], 0)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "norm, offset, ans",
        [
            ([1, 0, 0], 0, 0),
            ([1, 0, 0], 1.001, 1),
            ([1, 0, 0], -1.001, -1),
            ([1, 0, 0], 0.999, 0),
            ([1, 0, 0], -0.999, 0),
            ([0, 1, 0], 0, 0),
            ([0, 1, 0], 1.001, 1),
            ([0, 1, 0], -1.001, -1),
            ([0, 1, 0], 0.999, 0),
            ([0, 1, 0], -0.999, 0),
            ([0, 0, 1], 0, 0),
            ([0, 0, 1], 1.001, 1),
            ([0, 0, 1], -1.001, -1),
            ([0, 0, 1], 0.999, 0),
            ([0, 0, 1], -0.999, 0),
            ([1, 1, 1], -2.999, 0),
            ([1, 1, 1], -3.001, -1),
            ([1, 1, 1], 2.999, 0),
            ([1, 1, 1], 3.001, 1),
        ],
    )
    def test_box_test(self, box, norm, offset, ans):
        surf = Plane(norm, offset)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize("norm, offset", [([0, 0, 1], -2), ([1, 0, 0], -2), ([0, 1, 0], -2)])
    def test_transform(self, transform, norm, offset):
        ans_surf = Plane(norm, offset, transform=transform)
        surf = Plane(norm, offset).transform(transform)
        assert surf == ans_surf, (
            "Passing transformation through __init__ or method transform should be equivalent"
        )
        ans_surf_tr = ans_surf.apply_transformation()
        surf_tr = surf.apply_transformation()
        assert surf_tr == ans_surf_tr, (
            "Surfaces with applied transformation also should be equivalent (invariant)"
        )

    @pytest.mark.parametrize(
        "norm, offset, options",
        [
            ([0, 0, 1], -2, {}),
            ([1, 0, 0], -2, {"name": 3}),
            ([0, 1, 0], -2, {"name": 4, "comments": ["abc", "def"]}),
        ],
    )
    def test_pickle(self, transform, norm, offset, options):
        surf = Plane(norm, offset, transform=transform, **options)
        surf_un = pass_through_pickle(surf)
        assert surf.is_close_to(surf_un)
        np.testing.assert_array_almost_equal(surf._v, surf_un._v)
        np.testing.assert_almost_equal(surf._k, surf_un._k)
        if transform:
            surf = surf.apply_transformation()
            surf_un = pass_through_pickle(surf)
            surf_un.is_close_to(surf)
            np.testing.assert_array_almost_equal(surf._v, surf_un._v)
            np.testing.assert_almost_equal(surf._k, surf_un._k)
        assert surf.options == surf_un.options

    surfs: Final = [
        create_surface("PX", 5.0, name=1),  # 0
        create_surface("PX", 5.0 + 1.0e-12, name=1),  # 1
        create_surface("PX", 5.0 - 1.0e-12, name=1),  # 2
        create_surface("PX", 5.0 + 1.0e-11, name=1),  # 3
        create_surface("PY", 5.0, name=2),  # 4
        create_surface("PY", 5.0 + 1.0e-12, name=2),  # 5
        create_surface("PY", 5.0 - 1.0e-12, name=2),  # 6
        create_surface("PY", 5.0 + 1.0e-11, name=2),  # 7
        create_surface("PZ", 5.0, name=3),  # 8
        create_surface("PZ", 5.0 + 1.0e-12, name=3),  # 9
        create_surface("PZ", 5.0 - 1.0e-12, name=3),  # 10
        create_surface("PZ", 5.0 + 1.0e-11, name=3),  # 11
        create_surface("P", 1, 5.0e-13, -5.0e-13, 5.0, name=4),  # 12
        create_surface("P", -5.0e-13, 1, 5.0e-13, 5.0 + 1.0e-12, name=4),  # 13
        create_surface("P", 5.0e-13, -5.0e-13, 1, 5.0 - 1.0e-12, name=4),  # 14
        create_surface("P", 1, 1, 0, -4, name=5),  # 15
        create_surface("P", 2, 2, 0, -8, name=5),  # 16
    ]

    eq_matrix: Final = [
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_close(self, i1: int, s1: Plane, i2: int, s2: Plane) -> None:
        result = s1.is_close_to(s2)
        assert result == bool(self.eq_matrix[i1][i2])

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            assert hash(s1.round()) == hash(s2.round())

    @pytest.mark.parametrize("coeffs", [[0, 2, 1, 3], [4, -1, 2, 0], [-1, 0, 0, 5], [-4, -4, 3, 3]])
    def test_reverse(self, coeffs):
        plane = create_surface("P", *coeffs)
        answer = create_surface("P", *[-c for c in coeffs])
        assert plane.reverse() == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 PX 5",
                "1 PX 5",
                "1 PX 5",
                "1 PX 5.00000000001",
                "2 PY 5",
                "2 PY 5",
                "2 PY 5",
                "2 PY 5.00000000001",
                "3 PZ 5",
                "3 PZ 5",
                "3 PZ 5",
                "3 PZ 5.00000000001",
                "4 PX 5",
                "4 PY 5",
                "4 PZ 5",
                "5 P 0.707106781187 0.707106781187 0 -2.828427124746",
                "5 P 0.707106781187 0.707106781187 0 -2.828427124746",
            ],
            strict=False,
        ),
    )
    def test_mcnp_pretty_repr(self, surface, answer):
        # s = surface.round()
        s = surface
        desc = s.mcnp_repr(pretty=True)
        assert desc == answer
        # desc = s.mcnp_repr(pretty=False)
        # assert desc == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 PX 5",
                "1 PX 5",
                "1 PX 5",
                "1 PX 5.00000000001",
                "2 PY 5",
                "2 PY 5",
                "2 PY 5",
                "2 PY 5.00000000001",
                "3 PZ 5",
                "3 PZ 5",
                "3 PZ 5",
                "3 PZ 5.00000000001",
                "4 PX 5",
                "4 PY 5",
                "4 PZ 5",
                "5 P 0.707106781187 0.707106781187 0 -2.828427124746",
                "5 P 0.707106781187 0.707106781187 0 -2.828427124746",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr()
        assert desc == answer, (
            "Should print values exactly with 13 digits precision, and round integer values"
        )


class TestSphere:
    @pytest.mark.parametrize("center, radius, c, r", [([1, 2, 3], 5, np.array([1, 2, 3]), 5)])
    def test_init(self, transform, center, radius, c, r):
        surf = Sphere(center, radius, transform=transform).apply_transformation()
        c = transform.apply2point(c)
        np.testing.assert_array_almost_equal(c, surf._center)
        np.testing.assert_array_almost_equal(r, surf._radius)

    @pytest.mark.parametrize(
        "point, expected",
        [
            (np.array([1, 2, 3]), [-1]),
            (np.array([5.999, 2, 3]), [-1]),
            (np.array([6.001, 2, 3]), [+1]),
            (np.array([1, 6.999, 3]), [-1]),
            (np.array([1, 7.001, 3]), [+1]),
            (np.array([1, 2, 7.999]), [-1]),
            (np.array([1, 2, 8.001]), [+1]),
            (np.array([-3.999, 2, 3]), [-1]),
            (np.array([-4.001, 2, 3]), [+1]),
            (np.array([1, 2.999, 3]), [-1]),
            (np.array([1, -3.001, 3]), [+1]),
            (np.array([1, 2, -1.999]), [-1]),
            (np.array([1, 2, -2.001]), [+1]),
            (
                np.array(
                    [
                        [1, 2, 3],
                        [5.999, 2, 3],
                        [6.001, 2, 3],
                        [1, 6.999, 3],
                        [1, 7.001, 3],
                        [1, 2, 7.999],
                        [1, 2, 8.001],
                        [-3.999, 2, 3],
                        [-4.001, 2, 3],
                        [1, 2.999, 3],
                        [1, -3.001, 3],
                        [1, 2, -1.999],
                        [1, 2, -2.001],
                    ]
                ),
                np.array([-1, -1, +1, -1, +1, -1, +1, -1, +1, -1, +1, -1, +1]),
            ),
        ],
    )
    def test_point_test(self, point, expected):
        surf = Sphere([1, 2, 3], 5)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "center, radius, ans",
        [
            (np.array([0, 0, 0]), 1.8, -1),
            (np.array([0, 0, 0]), 1.7, 0),
            (np.array([0, 0, -2]), 0.999, +1),
            (np.array([0, 0, -2]), 1.001, 0),
            (np.array([-2, -2, -2]), 1.7, +1),
            (np.array([-2, -2, -2]), 1.8, 0),
            (np.array([-2, -2, -2]), 5.1, 0),
            (np.array([-2, -2, -2]), 5.2, -1),
            (np.array([-2, 0, -2]), 1.4, +1),
            (np.array([-2, 0, -2]), 1.5, 0),
            (np.array([-2, 0, -2]), 4.3, 0),
            (np.array([-2, 0, -2]), 4.4, -1),
        ],
    )
    def test_box_test(self, box, center, radius, ans):
        surf = Sphere(center, radius)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize("center, radius", [([1, 2, 3], 5)])
    def test_transform(self, transform, center, radius):
        ans_surf = Sphere(center, radius, transform=transform)
        surf = Sphere(center, radius)
        surf_tr = surf.transform(transform)
        np.testing.assert_array_almost_equal(ans_surf._center, surf_tr._center)
        np.testing.assert_almost_equal(ans_surf._radius, surf_tr._radius)

    @pytest.mark.parametrize(
        "center, radius, options",
        [
            ([1, 2, 3], 5, {}),
            ([1, 2, 3], 5, {"name": 2}),
            ([1, 2, 3], 5, {"name": 3, "comment": ["abc", "def"]}),
        ],
    )
    def test_pickle(self, center, radius, options):
        surf = Sphere(center, radius, **options)
        surf_un = pass_through_pickle(surf)
        np.testing.assert_array_almost_equal(surf._center, surf_un._center)
        np.testing.assert_almost_equal(surf._radius, surf_un._radius)
        assert surf.options == surf_un.options

    surfs: Final = [
        create_surface("SO", 1.0, name=1),  # 0
        create_surface("SO", 1.0 + 5.0e-13, name=1),  # 1
        create_surface("SO", 2.0, name=1),  # 2
        create_surface("SX", 5.0, 4.0, name=2),  # 3
        create_surface("SX", 5.0 + 1.0e-12, 4.0, name=2),  # 4
        create_surface("SX", 5.0 - 1.0e-12, 4.0 + 1.0e-12, name=2),  # 5
        create_surface("SY", 5.0, 4.0, name=2),  # 6
        create_surface("SY", 5.0 + 1.0e-12, 4.0, name=2),  # 7
        create_surface("SY", 5.0 - 1.0e-12, 4.0 + 1.0e-12, name=2),  # 8
        create_surface("SZ", 5.0, 4.0, name=2),  # 9
        create_surface("SZ", 5.0 + 1.0e-12, 4.0, name=2),  # 10
        create_surface("SZ", 5.0 - 1.0e-12, 4.0 + 1.0e-12, name=2),  # 11
        create_surface("S", 5.0, 1.0e-13, -1.0e-13, 4.0 + 1.0e-12, name=3),  # 12
        create_surface("S", 1.0e-13, 5.0, -1.0e-13, 4.0 - 1.0e-12, name=3),  # 13
        create_surface("S", 1.0e-13, -1.0e-13, 5.0, 4.0 + 1.0e-12, name=3),  # 14
        create_surface("S", 4.3, 8.2, -1.4, 3.5, name=4),  # 15
        create_surface(
            "S", 4.3 - 1.0e-12, 8.2 + 1.0e-12, -1.4 - 1.0e-12, 3.5 + 1.0e-12, name=4
        ),  # 16
    ]

    eq_matrix: Final = [
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_equality(self, i1, s1, i2, s2):
        s1, s2 = s1.round(), s2.round()
        if self.eq_matrix[i1][i2]:
            assert s1 == s2
        else:
            assert s1 != s2

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            assert hash(s1.round()) == hash(s2.round())

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 SO 1",
                "1 SO 1",
                "1 SO 2",
                "2 SX 5 4",
                "2 SX 5 4",
                "2 SX 5 4",
                "2 SY 5 4",
                "2 SY 5 4",
                "2 SY 5 4",
                "2 SZ 5 4",
                "2 SZ 5 4",
                "2 SZ 5 4",
                "3 SX 5 4",
                "3 SY 5 4",
                "3 SZ 5 4",
                "4 S 4.3 8.2 -1.4 3.5",
                "4 S 4.3 8.2 -1.4 3.5",
            ],
            strict=False,
        ),
    )
    def test_mcnp_pretty_repr(self, surface, answer):
        # s = surface.round()
        s = surface
        desc = s.mcnp_repr(pretty=True)
        assert desc == answer
        desc = s.mcnp_repr(pretty=False)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 SO 1",
                "1 SO 1",
                "1 SO 2",
                "2 SX 5 4",
                "2 SX 5 4",
                "2 SX 5 4",
                "2 SY 5 4",
                "2 SY 5 4",
                "2 SY 5 4",
                "2 SZ 5 4",
                "2 SZ 5 4",
                "2 SZ 5 4",
                "3 SX 5 4",
                "3 SY 5 4",
                "3 SZ 5 4",
                "4 S 4.3 8.2 -1.4 3.5",
                "4 S 4.3 8.2 -1.4 3.5",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr()
        assert desc == answer, "Should print exact values"


class TestCylinder:
    @pytest.mark.parametrize(
        "point, axis, radius, pt, ax, rad",
        [([1, 2, 3], [1, 2, 3], 5, [0, 0, 0], np.array([1, 2, 3]) / np.sqrt(14), 5)],
    )
    def test_init(self, transform, point, axis, radius, pt, ax, rad):
        surf = Cylinder(point, axis, radius, transform=transform).apply_transformation()
        pt = transform.apply2point(pt)
        ax = transform.apply2vector(ax)
        pt = pt - ax * np.dot(ax, pt)
        np.testing.assert_array_almost_equal(pt, surf._pt)
        np.testing.assert_array_almost_equal(ax, surf._axis)
        np.testing.assert_array_almost_equal(rad, surf._radius)

    @pytest.mark.parametrize(
        "point, expected",
        [
            ([0, 3, 4], [-1]),
            ([-2, 3, 2.001], [-1]),
            ([-3, 3, 1.999], [+1]),
            ([2, 3, 5.999], [-1]),
            ([3, 3, 6.001], [+1]),
            ([4, 1.001, 4], [-1]),
            ([-4, 0.999, 4], [+1]),
            ([-5, 4.999, 4], [-1]),
            ([5, 5.001, 4], [+1]),
            (
                np.array(
                    [
                        [0, 3, 4],
                        [-2, 3, 2.001],
                        [-3, 3, 1.999],
                        [2, 3, 5.999],
                        [3, 3, 6.001],
                        [4, 1.001, 4],
                        [-4, 0.999, 4],
                        [-5, 4.999, 4],
                        [5, 5.001, 4],
                    ]
                ),
                [-1, -1, +1, -1, +1, -1, +1, -1, +1],
            ),
        ],
    )
    def test_point_test(self, point, expected):
        surf = Cylinder([-1, 3, 4], [1, 0, 0], 2)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "point, axis, radius, ans",
        [
            ([0, 0, 0], [1, 0, 0], 0.5, 0),
            ([0, 0, 0], [1, 0, 0], 1.4, 0),
            ([0, 0, 0], [1, 0, 0], 1.5, -1),
            ([0, 1, 1], [1, 0, 0], 0.001, 0),
            ([0, 1, 1], [1, 0, 0], 2.8, 0),
            ([0, 1, 1], [1, 0, 0], 2.9, -1),
            ([0, 2, 0], [1, 0, 0], 0.999, +1),
            ([0, 2, 0], [1, 0, 0], 1.001, 0),
            ([0, 2, 0], [1, 0, 0], 3.1, 0),
            ([0, 2, 0], [1, 0, 0], 3.2, -1),
            ([0, 0, 0], [0, 1, 0], 0.5, 0),
            ([0, 0, 0], [0, 1, 0], 1.4, 0),
            ([0, 0, 0], [0, 1, 0], 1.5, -1),
            ([1, 0, 1], [0, 1, 0], 0.001, 0),
            ([1, 0, 1], [0, 1, 0], 2.8, 0),
            ([1, 0, 1], [0, 1, 0], 2.9, -1),
            ([2, 0, 0], [0, 1, 0], 0.999, +1),
            ([2, 0, 0], [0, 1, 0], 1.001, 0),
            ([2, 0, 0], [0, 1, 0], 3.1, 0),
            ([2, 0, 0], [0, 1, 0], 3.2, -1),
        ],
    )
    def test_box_test(self, box, point, axis, radius, ans):
        surf = Cylinder(point, axis, radius)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize(
        "point, axis, radius", [([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 5)]
    )
    def test_transform(self, transform, point, axis, radius):
        ans_surf = Cylinder(point, axis, radius, transform=transform)
        surf = Cylinder(point, axis, radius)
        surf_tr = surf.transform(transform)
        np.testing.assert_array_almost_equal(ans_surf._pt, surf_tr._pt)
        np.testing.assert_array_almost_equal(ans_surf._axis, surf_tr._axis)
        np.testing.assert_almost_equal(ans_surf._radius, surf_tr._radius)

    @pytest.mark.parametrize(
        "point, axis, radius, options",
        [
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 5, {}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 5, {"name": 1}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 5, {"name": 2}),
        ],
    )
    def test_pickle(self, point, axis, radius, options):
        surf = Cylinder(point, axis, radius, **options)
        surf_un = pass_through_pickle(surf)
        np.testing.assert_array_almost_equal(surf._pt, surf_un._pt)
        np.testing.assert_array_almost_equal(surf._axis, surf_un._axis)
        np.testing.assert_almost_equal(surf._radius, surf_un._radius)
        assert surf.options == surf_un.options

    surfs: Final = [
        create_surface("CX", 1.0, name=1),  # 0
        create_surface("CX", 1.0 + 5.0e-13, name=1),  # 1
        create_surface("CY", 1.0, name=1),  # 2
        create_surface("CY", 1.0 + 5.0e-13, name=1),  # 3
        create_surface("CZ", 1.0, name=1),  # 4
        create_surface("CZ", 1.0 + 5.0e-13, name=1),  # 5
        create_surface("C/X", 1, -2, 3, name=2),  # 6
        create_surface("C/X", 1 - 5.0e-13, -2 + 1.0e-12, 3 - 1.0e-12, name=2),  # 7
        create_surface("C/Y", 1, -2, 3, name=2),  # 8
        create_surface("C/Y", 1 - 5.0e-13, -2 + 1.0e-12, 3 - 1.0e-12, name=2),  # 9
        create_surface("C/Z", 1, -2, 3, name=2),  # 10
        create_surface("C/Z", 1 - 5.0e-13, -2 + 1.0e-12, 3 - 1.0e-12, name=2),  # 11
        Cylinder([0, 1, -2], [2, 1.0e-13, -1.0e-13], 3, name=3),  # 12
        Cylinder([5, 1, -2], [1 + 1.0e-13, -1.0e-13, 2.0e-13], 3, name=3),  # 13
        Cylinder([1, 0, -2], [1.0e-13, 2, -1.0e-13], 3, name=3),  # 14
        Cylinder([1, 5, -2], [-1.0e-13, 1 + 1.0e-13, 2.0e-13], 3, name=3),  # 15
        Cylinder([1, -2, 0], [1.0e-13, -1.0e-13, 2], 3, name=3),  # 16
        Cylinder([1, -2, 5], [-1.0e-13, 1.0e-13, 1 + 2.0e-13], 3, name=3),  # 17
        Cylinder([0, 1, -2], [-1, 1.0e-13, -1.0e-13], 3, name=4),  # 18
        Cylinder([1, 0, -2], [1.0e-13, -2, -1.0e-13], 3, name=4),  # 19
        Cylinder([1, -2, 0], [1.0e-13, 1.0e-13, -2], 3, name=4),  # 20
    ]

    eq_matrix: Final = [
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_equality(self, i1, s1, i2, s2):
        s1, s2 = s1.round(), s2.round()
        result = s1 == s2
        assert result == bool(self.eq_matrix[i1][i2])

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            assert hash(s1.round()) == hash(s2.round())

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 CX 1",
                "1 CX 1",
                "1 CY 1",
                "1 CY 1",
                "1 CZ 1",
                "1 CZ 1",
                "2 C/X 1 -2 3",
                "2 C/X 1 -2 3",
                "2 C/Y 1 -2 3",
                "2 C/Y 1 -2 3",
                "2 C/Z 1 -2 3",
                "2 C/Z 1 -2 3",
                "3 C/X 1 -2 3",
                "3 C/X 1 -2 3",
                "3 C/Y 1 -2 3",
                "3 C/Y 1 -2 3",
                "3 C/Z 1 -2 3",
                "3 C/Z 1 -2 3",
            ],
            strict=False,
        ),
    )
    def test_mcnp_prety_repr(self, surface, answer):
        desc = surface.round().mcnp_repr(True)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 CX 1",
                "1 CX 1",
                "1 CY 1",
                "1 CY 1",
                "1 CZ 1",
                "1 CZ 1",
                "2 C/X 1 -2 3",
                "2 C/X 1 -2 3",
                "2 C/Y 1 -2 3",
                "2 C/Y 1 -2 3",
                "2 C/Z 1 -2 3",
                "2 C/Z 1 -2 3",
                "3 C/X 1 -2 3",
                "3 C/X 1 -2 3",
                "3 C/Y 1 -2 3",
                "3 C/Y 1 -2 3",
                "3 C/Z 1 -2 3",
                "3 C/Z 1 -2 3",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr()
        if "\n" in desc:
            assert desc.split() == answer.split()
        else:
            assert desc == answer


class TestCone:
    @pytest.mark.parametrize(
        "apex, axis, tan2, ap, ax, t2",
        [
            (
                [1, 2, 3],
                [1, 2, 3],
                0.25,
                [1, 2, 3],
                np.array([1, 2, 3]) / np.sqrt(14),
                0.25,
            )
        ],
    )
    def test_init(self, transform, apex, axis, tan2, ap, ax, t2):
        surf = Cone(apex, axis, tan2, transform=transform).apply_transformation()
        ap = transform.apply2point(ap)
        ax = transform.apply2vector(ax)
        np.testing.assert_array_almost_equal(ap, surf._apex)
        np.testing.assert_array_almost_equal(ax, surf._axis)
        np.testing.assert_array_almost_equal(t2, surf._t2)

    @pytest.mark.parametrize("sheet, case", [(0, 0), (1, 1), (-1, 2)])
    @pytest.mark.parametrize(
        "point, expected",
        [
            ([0, 1, 2], ([-1], [-1], [+1])),
            ([0, 1, 0.3], ([-1], [-1], [+1])),
            ([0, 1, 0.2], ([+1], [+1], [+1])),
            ([0, 1, 3.7], ([-1], [-1], [+1])),
            ([0, 1, 3.8], ([+1], [+1], [+1])),
            ([0, 2.7, 2], ([-1], [-1], [+1])),
            ([0, 2.8, 2], ([+1], [+1], [+1])),
            ([0, -0.7, 2], ([-1], [-1], [+1])),
            ([0, -0.8, 2], ([+1], [+1], [+1])),
            ([-6, 1, 0.3], ([-1], [+1], [-1])),
            ([-6, 1, 0.2], ([+1], [+1], [+1])),
            ([-6, 1, 3.7], ([-1], [+1], [-1])),
            ([-6, 1, 3.8], ([+1], [+1], [+1])),
            ([-6, 2.7, 2], ([-1], [+1], [-1])),
            ([-6, 2.8, 2], ([+1], [+1], [+1])),
            ([-6, -0.7, 2], ([-1], [+1], [-1])),
            ([-6, -0.8, 2], ([+1], [+1], [+1])),
            ([3, 1, -1.4], ([-1], [-1], [+1])),
            ([3, 1, -1.5], ([+1], [+1], [+1])),
            ([3, 1, 5.4], ([-1], [-1], [+1])),
            ([3, 1, 5.5], ([+1], [+1], [+1])),
            ([3, 4.4, 2], ([-1], [-1], [+1])),
            ([3, 4.5, 2], ([+1], [+1], [+1])),
            ([3, -2.4, 2], ([-1], [-1], [+1])),
            ([3, -2.5, 2], ([+1], [+1], [+1])),
            (
                np.array(
                    [
                        [0, 1, 2],
                        [0, 1, 0.3],
                        [0, 1, 0.2],
                        [0, 1, 3.7],
                        [0, 1, 3.8],
                        [0, 2.7, 2],
                        [0, 2.8, 2],
                        [0, -0.7, 2],
                        [0, -0.8, 2],
                        [-6, 1, 0.3],
                        [-6, 1, 0.2],
                        [-6, 1, 3.7],
                        [-6, 1, 3.8],
                        [-6, 2.7, 2],
                        [-6, 2.8, 2],
                        [-6, -0.7, 2],
                        [-6, -0.8, 2],
                        [3, 1, -1.4],
                        [3, 1, -1.5],
                        [3, 1, 5.4],
                        [3, 1, 5.5],
                        [3, 4.4, 2],
                        [3, 4.5, 2],
                        [3, -2.4, 2],
                        [3, -2.5, 2],
                    ]
                ),
                (
                    [
                        -1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                    ],
                    [
                        -1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                    ],
                    [
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        -1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                        +1,
                    ],
                ),
            ),
        ],
    )
    def test_point_test(self, sheet, case, point, expected):
        surf = Cone([-3, 1, 2], [1, 0, 0], 1.0 / 3.0, sheet)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected[case])

    @pytest.mark.parametrize(
        "params",
        [
            ([0, 0, 0], [1, 0, 0], 0.25, 0),
            ([0, 0, 0], [1, 0, 0], 0.25, -1, 0),
            ([0, 0, 0], [1, 0, 0], 0.25, +1, 0),
            ([0, 1.4, 0], [1, 0, 0], 0.25, 0),
            ([0, 1.4, 0], [1, 0, 0], 0.25, -1, 0),
            ([0, 1.4, 0], [1, 0, 0], 0.25, +1, 0),
            ([0, 1.6, 0], [1, 0, 0], 0.25, +1),
            ([0, 1.6, 0], [1, 0, 0], 0.25, -1, +1),
            ([0, 1.6, 0], [1, 0, 0], 0.25, +1, +1),
            ([0, -1.4, 0], [1, 0, 0], 0.25, 0),
            ([0, -1.4, 0], [1, 0, 0], 0.25, -1, 0),
            ([0, -1.4, 0], [1, 0, 0], 0.25, +1, 0),
            ([0, -1.6, 0], [1, 0, 0], 0.25, +1),
            ([0, -1.6, 0], [1, 0, 0], 0.25, -1, +1),
            ([0, -1.6, 0], [1, 0, 0], 0.25, +1, +1),
            ([-1, 1.9, 0], [1, 0, 0], 0.25, 0),
            ([-1, 1.9, 0], [1, 0, 0], 0.25, -1, +1),
            ([-1, 1.9, 0], [1, 0, 0], 0.25, +1, 0),
            ([1, 2.1, 0], [1, 0, 0], 0.25, +1),
            ([1, 2.1, 0], [1, 0, 0], 0.25, -1, +1),
            ([1, 2.1, 0], [1, 0, 0], 0.25, +1, +1),
            ([3.9, 0, 0], [1, 0, 0], 0.25, -1),
            ([3.9, 0, 0], [1, 0, 0], 0.25, -1, -1),
            ([3.9, 0, 0], [1, 0, 0], 0.25, +1, +1),
            ([-3.9, 0, 0], [1, 0, 0], 0.25, -1),
            ([-3.9, 0, 0], [1, 0, 0], 0.25, -1, +1),
            ([-3.9, 0, 0], [1, 0, 0], 0.25, +1, -1),
            ([0, 0, -3.9], [0, 0, 1], 0.25, -1),
            ([0, 0, -3.9], [0, 0, 1], 0.25, -1, +1),
            ([0, 0, -3.9], [0, 0, 1], 0.25, +1, -1),
            ([0, 0, 3.9], [0, 0, 1], 0.25, -1),
            ([0, 0, 3.9], [0, 0, 1], 0.25, -1, -1),
            ([0, 0, 3.9], [0, 0, 1], 0.25, +1, +1),
            ([0, -3.9, 0], [0, 1, 0], 0.25, -1),
            ([0, -3.9, 0], [0, 1, 0], 0.25, -1, +1),
            ([0, -3.9, 0], [0, 1, 0], 0.25, +1, -1),
            ([3.8, 0, 0], [1, 0, 0], 0.25, 0),
            ([3.8, 0, 0], [1, 0, 0], 0.25, -1, 0),
            ([3.8, 0, 0], [1, 0, 0], 0.25, +1, +1),
            ([-3.8, 0, 0], [1, 0, 0], 0.25, 0),
            ([-3.8, 0, 0], [1, 0, 0], 0.25, -1, +1),
            ([-3.8, 0, 0], [1, 0, 0], 0.25, +1, 0),
            ([0, 0, -3.8], [0, 0, 1], 0.25, 0),
            ([0, 0, -3.8], [0, 0, 1], 0.25, -1, +1),
            ([0, 0, -3.8], [0, 0, 1], 0.25, +1, 0),
            ([0, 0, 3.8], [0, 0, 1], 0.25, 0),
            ([0, 0, 3.8], [0, 0, 1], 0.25, -1, 0),
            ([0, 0, 3.8], [0, 0, 1], 0.25, +1, +1),
            ([0, -3.8, 0], [0, 1, 0], 0.25, 0),
            ([0, -3.8, 0], [0, 1, 0], 0.25, -1, +1),
            ([0, -3.8, 0], [0, 1, 0], 0.25, +1, 0),
        ],
    )
    def test_box_test(self, box, params):
        *param, ans = params
        surf = Cone(*param)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize(
        "apex, axis, t2", [([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25)]
    )
    def test_transform(self, transform, apex, axis, t2):
        ans_surf = Cone(apex, axis, t2, transform=transform)
        surf = Cone(apex, axis, t2)
        surf_tr = surf.transform(transform)
        self.assert_cone(ans_surf, surf_tr)

    @staticmethod
    def assert_cone(ans_surf, surf_tr):
        np.testing.assert_array_almost_equal(ans_surf._apex, surf_tr._apex)
        np.testing.assert_array_almost_equal(ans_surf._axis, surf_tr._axis)
        np.testing.assert_almost_equal(ans_surf._t2, surf_tr._t2)
        assert ans_surf._sheet == surf_tr._sheet
        assert ans_surf.options == surf_tr.options

    @pytest.mark.parametrize(
        "apex, axis, t2, sheet, options",
        [
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, 0, {"name": 1}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, 0, {}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, -1, {"name": 1}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, -1, {}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, +1, {"name": 1}),
            ([1, 2, 3], np.array([1, 2, 3]) / np.sqrt(14), 0.25, +1, {}),
        ],
    )
    def test_pickle(self, apex, axis, t2, sheet, options):
        surf = Cone(apex, axis, t2, sheet, **options)
        surf_un = pass_through_pickle(surf)
        self.assert_cone(surf, surf_un)

    surfs: Final = [
        create_surface("KX", 4, 0.25, name=1),  # 0
        create_surface("KX", 4 - 1.0e-12, 0.25 + 1.0e-13, name=1),  # 1
        create_surface("KY", 4, 0.25, name=1),  # 2
        create_surface("KY", 4 - 1.0e-12, 0.25 + 1.0e-13, name=1),  # 3
        create_surface("KZ", 4, 0.25, name=1),  # 4
        create_surface("KZ", 4 - 1.0e-12, 0.25 + 1.0e-13, name=1),  # 5
        create_surface("K/X", 3, 2, -4, 0.25, name=2),  # 6
        create_surface("K/X", 3 - 1.0e-12, 2 + 1.0e-12, -4 + 1.0e-12, 0.25 - 1.0e-13, name=2),  # 7
        create_surface("K/Y", 3, 2, -4, 0.25, name=2),  # 8
        create_surface("K/Y", 3 - 1.0e-12, 2 + 1.0e-12, -4 + 1.0e-12, 0.25 - 1.0e-13, name=2),  # 9
        create_surface("K/Z", 3, 2, -4, 0.25, name=2),  # 10
        create_surface("K/Z", 3 - 1.0e-12, 2 + 1.0e-12, -4 + 1.0e-12, 0.25 - 1.0e-13, name=2),  # 11
        Cone([3, 2, -4], [1, 1.0e-13, -1.0e-13], 0.25, name=3),  # 12
        Cone([3, 2, -4], [1.0e-13, 1, -1.0e-13], 0.25, name=3),  # 13
        Cone([3, 2, -4], [1.0e-13, -1.0e-13, 1], 0.25, name=3),  # 14
        Cone([3, 2, -4], [-1, 1.0e-13, -1.0e-13], 0.25, name=4),  # 15
        Cone([3, 2, -4], [1.0e-13, -1, -1.0e-13], 0.25, name=4),  # 16
        Cone([3, 2, -4], [1.0e-13, -1.0e-13, -1], 0.25, name=4),  # 17
        create_surface("K/X", 3, 2, -4, 0.25, 1, name=5),  # 18
        create_surface(
            "K/X",
            3 - 1.0e-12,
            2 + 1.0e-12,
            -4 + 1.0e-12,
            0.25 - 1.0e-13,  # 19
            1,
            name=5,
        ),
        create_surface("K/Y", 3, 2, -4, 0.25, 1, name=5),  # 20
        create_surface(
            "K/Y",
            3 - 1.0e-12,
            2 + 1.0e-12,
            -4 + 1.0e-12,
            0.25 - 1.0e-13,  # 21
            1,
            name=5,
        ),
        create_surface("K/Z", 3, 2, -4, 0.25, 1, name=5),  # 22
        create_surface(
            "K/Z",
            3 - 1.0e-12,
            2 + 1.0e-12,
            -4 + 1.0e-12,
            0.25 - 1.0e-13,  # 23
            1,
            name=5,
        ),
        Cone([3, 2, -4], [1, 1.0e-13, -1.0e-13], 0.25, sheet=1, name=6),  # 24
        Cone([3, 2, -4], [1.0e-13, 1, -1.0e-13], 0.25, sheet=1, name=6),  # 25
        Cone([3, 2, -4], [1.0e-13, -1.0e-13, 1], 0.25, sheet=1, name=6),  # 26
        Cone([3, 2, -4], [-1, 1.0e-13, -1.0e-13], 0.25, sheet=1, name=7),  # 27
        Cone([3, 2, -4], [1.0e-13, -1, -1.0e-13], 0.25, sheet=1, name=7),  # 28
        Cone([3, 2, -4], [1.0e-13, -1.0e-13, -1], 0.25, sheet=1, name=7),  # 29
    ]

    @pytest.mark.parametrize("surf", surfs)
    @pytest.mark.parametrize("box", [Box([3, 2, -4], 10, 10, 10)])
    def test_transform2(self, transform, surf, box):
        points = box.generate_random_points(10000)
        test = surf.test_points(points)
        new_pts = transform.apply2point(points)
        new_surf = surf.transform(transform)
        new_test = new_surf.test_points(new_pts)
        np.testing.assert_array_equal(test, new_test)

    eq_matrix: Final = [
        [
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
        ],
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
        ],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_equality(self, i1, s1, i2, s2):
        if i1 < i2:
            s1, s2 = s1.round(), s2.round()
            if self.eq_matrix[i1][i2]:
                assert s1 == s2, f"Rounded surfaces {i1} and {i2}, should be equal "
                assert s2 == s1, "Equality result shouldn't depend on order"
            else:
                assert s1 != s2, f"Rounded surfaces {i1} and {i2}, should not be equal "
                assert s2 != s1, "Inequality result shouldn't depend on order"

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_hash(self, i1, s1, i2, s2):
        if i1 < i2:
            s1, s2 = s1.round(), s2.round()
            if self.eq_matrix[i1][i2]:
                assert hash(s1) == hash(s2), "The hash should be equal for equal objects"

    @pytest.mark.parametrize("surf", surfs)
    def test_copy(self, surf):
        copied_surf = surf.copy()
        assert surf == copied_surf, "The copy should be exactly equal to the original"
        assert copied_surf == surf, "Equality result shouldn't depend on order"

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 KX 4 0.25",
                "1 KX 4 0.25",
                "1 KY 4 0.25",
                "1 KY 4 0.25",
                "1 KZ 4 0.25",
                "1 KZ 4 0.25",
                "2 K/X 3 2 -4 0.25",
                "2 K/X 3 2 -4 0.25",
                "2 K/Y 3 2 -4 0.25",
                "2 K/Y 3 2 -4 0.25",
                "2 K/Z 3 2 -4 0.25",
                "2 K/Z 3 2 -4 0.25",
                "3 K/X 3 2 -4 0.25",
                "3 K/Y 3 2 -4 0.25",
                "3 K/Z 3 2 -4 0.25",
                "4 K/X 3 2 -4 0.25",
                "4 K/Y 3 2 -4 0.25",
                "4 K/Z 3 2 -4 0.25",
                "5 K/X 3 2 -4 0.25 1",
                "5 K/X 3 2 -4 0.25 1",
                "5 K/Y 3 2 -4 0.25 1",
                "5 K/Y 3 2 -4 0.25 1",
                "5 K/Z 3 2 -4 0.25 1",
                "5 K/Z 3 2 -4 0.25 1",
                "6 K/X 3 2 -4 0.25 1",
                "6 K/Y 3 2 -4 0.25 1",
                "6 K/Z 3 2 -4 0.25 1",
                "7 K/X 3 2 -4 0.25 -1",
                "7 K/Y 3 2 -4 0.25 -1",
                "7 K/Z 3 2 -4 0.25 -1",
            ],
            strict=False,
        ),
    )
    def test_mcnp_pretty_repr(self, surface, answer):
        s = surface.round()
        desc = s.mcnp_repr(pretty=True)
        assert desc == answer
        desc = s.mcnp_repr(pretty=False)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 KX 4 0.25",
                "1 KX 4 0.25",
                "1 KY 4 0.25",
                "1 KY 4 0.25",
                "1 KZ 4 0.25",
                "1 KZ 4 0.25",
                "2 K/X 3 2 -4 0.25",
                "2 K/X 3 2 -4 0.25",
                "2 K/Y 3 2 -4 0.25",
                "2 K/Y 3 2 -4 0.25",
                "2 K/Z 3 2 -4 0.25",
                "2 K/Z 3 2 -4 0.25",
                "3 K/X 3 2 -4 0.25",
                "3 K/Y 3 2 -4 0.25",
                "3 K/Z 3 2 -4 0.25",
                "4 K/X 3 2 -4 0.25",
                "4 K/Y 3 2 -4 0.25",
                "4 K/Z 3 2 -4 0.25",
                "5 K/X 3 2 -4 0.25 1",
                "5 K/X 3 2 -4 0.25 1",
                "5 K/Y 3 2 -4 0.25 1",
                "5 K/Y 3 2 -4 0.25 1",
                "5 K/Z 3 2 -4 0.25 1",
                "5 K/Z 3 2 -4 0.25 1",
                "6 K/X 3 2 -4 0.25 1",
                "6 K/Y 3 2 -4 0.25 1",
                "6 K/Z 3 2 -4 0.25 1",
                "7 K/X 3 2 -4 0.25 -1",
                "7 K/Y 3 2 -4 0.25 -1",
                "7 K/Z 3 2 -4 0.25 -1",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr()
        assert_mcnp_repr(desc, answer)


class TestTorus:
    @pytest.mark.parametrize(
        "center, axis, R, A, B, c, ax, r, a, b",
        [([1, 2, 3], [0, 0, 1], 4, 2, 1, [1, 2, 3], [0, 0, 1], 4, 2, 1)],
    )
    def test_init(self, transform, center, axis, R, A, B, c, ax, r, a, b):
        surf = Torus(center, axis, R, A, B, transform=transform).round()
        c = transform.apply2point(c)
        ax = transform.apply2vector(ax)
        np.testing.assert_array_almost_equal(c, surf._center)
        np.testing.assert_array_almost_equal(ax, surf._axis)
        np.testing.assert_array_almost_equal(r, surf._R)
        np.testing.assert_almost_equal(a, surf._a)
        np.testing.assert_almost_equal(b, surf._b)

    @pytest.fixture
    def torus(self, request):
        return [
            Torus([0, 0, 0], [1, 0, 0], 4, 2, 1),
            Torus([0, 0, 0], [1, 0, 0], -1, 1, 2),
            Torus([0, 0, 0], [1, 0, 0], 1, 1, 2),
        ]

    @pytest.mark.parametrize(
        "case_no, point, expected",
        [
            (0, [0, 0, 0], [1]),
            (0, [0, 0, 2.99], [1]),
            (0, [0, 0, 5.01], [1]),
            (0, [0, 0, 3.01], [-1]),
            (0, [0, 0, 4.99], [-1]),
            (0, [0, 2.99, 0], [1]),
            (0, [0, 5.01, 0], [1]),
            (0, [0, 3.01, 0], [-1]),
            (0, [0, 4.99, 0], [-1]),
            (0, [2.01, 0, 4], [1]),
            (0, [1.99, 0, 4], [-1]),
            (0, [2.01, 4, 0], [1]),
            (0, [1.99, 4, 0], [-1]),
            (
                0,
                np.array(
                    [
                        [0, 0, 0],
                        [0, 0, 2.99],
                        [0, 0, 5.01],
                        [0, 0, 3.01],
                        [0, 0, 4.99],
                        [0, 2.99, 0],
                        [0, 5.01, 0],
                        [0, 3.01, 0],
                        [0, 4.99, 0],
                        [2.01, 0, 4],
                        [1.99, 0, 4],
                        [2.01, 4, 0],
                        [1.99, 4, 0],
                    ]
                ),
                [1, 1, 1, -1, -1, 1, 1, -1, -1, 1, -1, 1, -1],
            ),
            (1, [0, 0, 0], [-1]),
            (1, [0, 0.999, 0], [-1]),
            (1, [0, 1.001, 0], [+1]),
            (1, [0, 2.999, 0], [+1]),
            (1, [0, 3.001, 0], [+1]),
            (2, [0, 0, 0], [-1]),
            (2, [0, 0.999, 0], [-1]),
            (2, [0, 1.001, 0], [-1]),
            (2, [0, 2.999, 0], [-1]),
            (2, [0, 3.001, 0], [+1]),
        ],
    )
    def test_point_test(self, torus, case_no, point, expected):
        surf = torus[case_no]
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "point, axis, radius, a, b, ans",
        [
            ([0, 0, 0], [1, 0, 0], 1, 0.5, 0.5, 0),
            ([0, 0, 0], [1, 0, 0], 1.91, 0.5, 0.5, 0),
            ([0, 0, 0], [1, 0, 0], 1.92, 0.5, 0.5, +1),
            ([1.4, 0, 0], [1, 0, 0], 1, 0.5, 0.5, 0),
            ([1.6, 0, 0], [1, 0, 0], 1, 0.5, 0.5, +1),
            ([0.5, 3, 0], [1, 0, 0], 1.6, 0.5, 0.5, 0),
            ([0.5, 3, 0], [1, 0, 0], 1.4, 0.5, 0.5, +1),
            ([0, 3, 0], [1, 0, 0], 3, 1.4, 1.4, 0),
            ([0, 3, 0], [1, 0, 0], 3, 1.55, 1.55, -1),
            ([0, 0, 0], [1, 0, 0], 1, 1.4, 1.4, 0),
            ([0, 0, 0], [1, 0, 0], 1, 1.5, 1.5, -1),
            ([0, 0, 0], [1, 0, 0], -1, 1.4, 1.4, 0),
            ([0, 0, 0], [1, 0, 0], -1, 2.6, 2.6, 0),
            ([0, 0, 0], [1, 0, 0], -1, 2.7, 2.7, -1),
            ([0, 0, 0], [1, 0, 0], 1.41, 1.42, 2, -1),
            ([0, 0, 0], [1, 0, 0], 1.41, 1.40, 2, 0),
            ([0, 0, 0], [0, 1, 1], 2.2, 0.5, 0.5, 0),
            ([0, 0, 0], [0, 1, 1], 2.3, 0.5, 0.5, +1),
            ([0, 0, 0], [1, 1, 1], 1, 1.9, 1.9, 0),
            ([0, 0, 0], [1, 1, 1], 1, 2.1, 2.1, -1),
            ([0, 0, 0], [0, 1, 0], 1, 0.5, 0.5, 0),
            ([0, 0, 0], [0, 1, 0], 1.91, 0.5, 0.5, 0),
            ([0, 0, 0], [0, 1, 0], 1.92, 0.5, 0.5, +1),
            ([0, 1.4, 0], [0, 1, 0], 1, 0.5, 0.5, 0),
            ([0, 1.6, 0], [0, 1, 0], 1, 0.5, 0.5, +1),
            ([3, 0.5, 0], [0, 1, 0], 1.6, 0.5, 0.5, 0),
            ([3, 0.5, 0], [0, 1, 0], 1.4, 0.5, 0.5, +1),
            ([3, 0, 0], [0, 1, 0], 3, 1.4, 1.4, 0),
            ([3, 0, 0], [0, 1, 0], 3, 1.55, 1.55, -1),
            ([0, 0, 0], [0, 1, 0], 1, 1.4, 1.4, 0),
            ([0, 0, 0], [0, 1, 0], 1, 1.5, 1.5, -1),
        ],
    )
    def test_box_test(self, box, point, axis, radius, a, b, ans):
        surf = Torus(point, axis, radius, a, b)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize("point, axis, radius, a, b", [([1, 2, 3], [0, 0, 1], 4, 2, 1)])
    def test_transform(self, transform, point, axis, radius, a, b):
        ans_surf = Torus(point, axis, radius, a, b, transform=transform)
        surf = Torus(point, axis, radius, a, b)
        surf_tr = surf.transform(transform)
        self.assert_torus(ans_surf, surf_tr)

    @staticmethod
    def assert_torus(ans_surf, surf_tr):
        np.testing.assert_array_almost_equal(ans_surf._center, surf_tr._center)
        np.testing.assert_array_almost_equal(ans_surf._axis, surf_tr._axis)
        np.testing.assert_almost_equal(ans_surf._R, surf_tr._R)
        np.testing.assert_almost_equal(ans_surf._a, surf_tr._a)
        np.testing.assert_almost_equal(ans_surf._b, surf_tr._b)
        assert surf_tr.options == ans_surf.options

    @pytest.mark.parametrize(
        "point, axis, radius, a, b, options",
        [
            ([1, 2, 3], [0, 0, 1], 4, 2, 1, {}),
            ([1, 2, 3], [0, 0, 1], 4, 2, 1, {"name": 4}),
        ],
    )
    def test_pickle(self, point, axis, radius, a, b, options):
        surf = Torus(point, axis, radius, a, b, **options)
        surf_un = pass_through_pickle(surf)
        self.assert_torus(surf, surf_un)

    surfs: Final = [
        Torus([1, 2, 3], [1, 0, 0], 4, 2, 1, name=1),
        Torus(
            [1 - 1.0e-13, 2 + 1.0e-12, 3 - 1.0e-12],
            [1, 1.0e-13, -3e-13],
            4 - 1.0e-12,
            2 + 1.0e-13,
            1 - 5.0e-13,
            name=1,
        ),
        Torus([1, 2, 3], [-1, 0, 0], 4, 2, 1, name=1),
        Torus([1, 2, 3], [0, 2, 0], 4, 2, 1, name=2),
        Torus(
            [1 - 1.0e-13, 2 + 1.0e-12, 3 - 1.0e-12],
            [1.0e-13, 1, -3e-13],
            4 - 1.0e-12,
            2 + 1.0e-13,
            1 - 5.0e-13,
            name=2,
        ),
        Torus([1, 2, 3], [0, -1, 0], 4, 2, 1, name=2),
        Torus([1, 2, 3], [0, 0, 1], 4, 2, 1, name=3),
        Torus(
            [1 - 1.0e-13, 2 + 1.0e-12, 3 - 1.0e-12],
            [1.0e-13, -3e-13, 3],
            4 - 1.0e-12,
            2 + 1.0e-13,
            1 - 5.0e-13,
            name=3,
        ),
        Torus([1, 2, 3], [0, 0, -1], 4, 2, 1, name=3),
    ]

    eq_matrix: Final = [
        [1, 1, 1, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 1, 1, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_equality(self, i1, s1, i2, s2):
        if i1 < i2:
            s1, s2 = s1.round(), s2.round()
            if self.eq_matrix[i1][i2]:
                assert s1 == s2
            else:
                assert s1 != s2

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            s1, s2 = s1.round(), s2.round()
            assert hash(s1) == hash(s2)

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 TX 1 2 3 4 2 1",
                "1 TX 1 2 3 4 2 1",
                "1 TX 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
            ],
            strict=False,
        ),
    )
    def test_mcnp_round_repr(self, surface, answer):
        desc = surface.round().mcnp_repr(pretty=True)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 TX 1 2 3 4 2 1",
                "1 TX 1 2 3 4 2 1",
                "1 TX 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "2 TY 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
                "3 TZ 1 2 3 4 2 1",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr()
        if "\n" in desc:
            assert desc.split() == answer.split()
        else:
            assert desc == answer


class TestGQuadratic:
    @pytest.mark.parametrize(
        "m, v, k, _m, _v, _k",
        [
            (
                [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
                [1, 2, 3],
                -4,
                np.diag([1, 2, 3]),
                [1, 2, 3],
                -4,
            )
        ],
    )
    def test_init(self, transform, m, v, k, _m, _v, _k):
        surf = GQuadratic(m, v, k, transform=transform).apply_transformation()
        _m, _v, _k = transform.apply2gq(_m, _v, _k)
        np.testing.assert_array_almost_equal(_m, surf._m)
        np.testing.assert_array_almost_equal(_v, surf._v)
        np.testing.assert_array_almost_equal(_k, surf._k)

    @pytest.mark.parametrize(
        "point, expected",
        [
            (np.array([0, 0, 0]), [-1]),
            (np.array([-0.999, 0, 0]), [-1]),
            (np.array([0.999, 0, 0]), [-1]),
            (np.array([-1.001, 0, 0]), [+1]),
            (np.array([1.001, 0, 0]), [+1]),
            (np.array([0, 0.999, 0]), [-1]),
            (np.array([0, 1.001, 0]), [+1]),
            (np.array([0, 0, -0.999]), [-1]),
            (
                np.array(
                    [
                        [0, 0, 0],
                        [-0.999, 0, 0],
                        [0.999, 0, 0],
                        [-1.001, 0, 0],
                        [1.001, 0, 0],
                        [0, 0.999, 0],
                        [0, 1.001, 0],
                        [0, 0, -0.999],
                    ]
                ),
                np.array([-1, -1, -1, 1, 1, -1, 1, -1]),
            ),
        ],
    )
    def test_point_test(self, point, expected):
        surf = GQuadratic(np.diag([1, 1, 1]), [0, 0, 0], -1)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize("mult", [1, 1e3, 1e7, 1.0e-3, 1.0e-7])
    @pytest.mark.parametrize(
        "m, v, k, ans",
        [
            (np.diag([1, 1, 1]), np.array([0, 0, 0]), -1, 0),
            (np.diag([1, 1, 1]), np.array([0, 0, 0]), -0.1, 0),
            (np.diag([1, 1, 1]), np.array([0, 0, 0]), -3.01, -1),
            (np.diag([1, 1, 1]), -2 * np.array([1, 1, 1]), 3 - 0.1, 0),
            (np.diag([1, 1, 1]), -2 * np.array([2, 2, 2]), 12 - 3.01, 0),
            (np.diag([1, 1, 1]), -2 * np.array([2, 2, 2]), 12 - 2.99, +1),
            (np.diag([1, 1, 1]), -2 * np.array([2, 0, 0]), 4 - 1.01, 0),
            (np.diag([1, 1, 1]), -2 * np.array([2, 0, 0]), 4 - 0.99, +1),
            (np.diag([1, 1, 1]), -2 * np.array([100, 0, 100]), 20000 - 2, +1),
        ],
    )
    def test_box_test(self, box, m, v, k, ans, mult):
        surf = GQuadratic(m * mult, v * mult, k * mult)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize("m, v, k", [(np.diag([1, 2, 3]), [1, 2, 3], -4)])
    def test_transform(self, transform, m, v, k):
        ans_surf = GQuadratic(m, v, k, transform=transform)
        surf = GQuadratic(m, v, k)
        surf_tr = surf.transform(transform)
        self.assert_gq(ans_surf, surf_tr)
        self.assert_gq(ans_surf.apply_transformation(), surf_tr.apply_transformation())

    @staticmethod
    def assert_gq(ans_surf, surf_tr):
        # np.testing.assert_array_almost_equal(ans_surf._m, surf_tr._m)
        # np.testing.assert_array_almost_equal(ans_surf._v, surf_tr._v)
        # np.testing.assert_almost_equal(ans_surf._k, surf_tr._k)
        assert surf_tr == ans_surf
        assert surf_tr.options == ans_surf.options
        # TODO dvp: move out of class and generalize for all the surfaces

    @pytest.mark.parametrize(
        "m, v, k, options",
        [
            (np.diag([1, 2, 3]), [1, 2, 3], -4, {}),
            (np.diag([1, 2, 3]), [1, 2, 3], -4, {"name": 5}),
        ],
    )
    def test_pickle(self, m, v, k, options):
        surf = GQuadratic(m, v, k, **options)
        surf_un = pass_through_pickle(surf)
        self.assert_gq(surf, surf_un)

    surfs: Final = [
        GQuadratic(np.diag([1, 1, 1]), -2 * np.array([1, 1, 1]), 3, name=1),
        GQuadratic(
            np.diag([1, 1, 1]) + 1.0e-13,
            -2 * np.array([1, 1, 1]) + 1.0e-13,
            3 - 1.0e-13,
            name=1,
        ),
        GQuadratic(-np.diag([1, 1, 1]), 2 * np.array([1, 1, 1]), -3, name=1),
        GQuadratic([[1, 0.25, 0.3], [0.25, 2, 0.4], [0.3, 0.4, 3]], [1, 2, 3], -4, name=2),
        GQuadratic(
            [[-1, -0.25, -0.3], [-0.25, -2, -0.4], [-0.3, -0.4, -3]],
            [-1, -2, -3],
            4,
            name=2,
        ),
        GQuadratic(
            np.array([[1, 0.25, 0.3], [0.25, 2, 0.4], [0.3, 0.4, 3]]) - 1.0e-13,
            np.array([1, 2, 3]) + 5.0e-13,
            -4 + 2e-12,
            name=2,
        ),
    ]

    eq_matrix: Final = [
        [1, 1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_round_equality(self, i1, s1, i2, s2):
        s1, s2 = s1.round(), s2.round()
        if self.eq_matrix[i1][i2]:
            assert s1 == s2
        else:
            assert s1 != s2

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            s1, s2 = s1.round(), s2.round()
            assert hash(s1) == hash(s2)

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 GQ 1 1 1 0 0 0 -2 -2 -2 3",
                "1 GQ 1 1 1 0 0 0 -2 -2 -2 3",
                "1 GQ -1 -1 -1 0 0 0 2 2 2 -3",
                "2 GQ 1 2 3 0.5 0.8 0.6 1 2 3 -4",
                "2 GQ -1 -2 -3 -0.5 -0.8 -0.6 -1 -2 -3 4",
                "2 GQ 1 2 3 0.5 0.8 0.6 1 2 3 -4",
            ],
            strict=False,
        ),
    )
    def test_mcnp_pretty_repr(self, surface, answer):
        desc = surface.mcnp_repr(pretty=True)
        assert desc == answer
        desc = surface.round().mcnp_repr(pretty=False)
        assert desc == answer


class TestBOX:
    @pytest.mark.parametrize(
        "center, dirx, diry, dirz",
        [
            ([0, 0, 1], [2, 0, 0], [0, 3, 0], [0, 0, 4]),
            ([1, 0, 0], [-2, 0, 0], [0, 3, 0], [0, 0, -4]),
            ([0, 1, 0], [10, 0, 0], [0, -5, 0], [0, 0, -6]),
        ],
    )
    def test_init(self, transform, center, dirx, diry, dirz):
        surf = BOX(center, dirx, diry, dirz, transform=transform)
        c = transform.apply2point(center)
        dx = transform.apply2vector(dirx)
        dy = transform.apply2vector(diry)
        dz = transform.apply2vector(dirz)
        ac, adx, ady, adz = surf.get_params()
        np.testing.assert_array_almost_equal(c, ac)
        np.testing.assert_array_almost_equal(dx, adx)
        np.testing.assert_array_almost_equal(dy, ady)
        np.testing.assert_array_almost_equal(dz, adz)

    @pytest.mark.parametrize(
        "point, expected",
        [
            ([1, 0.1, 0.1], [-1]),
            ([-1, 0.1, 0.1], [+1]),
            ([0.1, 0.5, 0.1], [-1]),
            ([0.1, -0.5, 0.2], [+1]),
            ([0.1, 0.2, 0.2], [-1]),
            ([-0.1, 0.2, 0.2], [+1]),
            ([1.0e-6, 100, -300], [+1]),
            ([-1.0e-6, 200, -500], [+1]),
            ([2.1, 0.1, 0.1], [+1]),
            ([1.9, 0.2, 0.2], [-1]),
            ([0.1, 1.1, 0.2], [+1]),
            ([0.2, 0.1, 0.6], [+1]),
            ([0.1, 0.1, 0.4], [-1]),
        ],
    )
    def test_point_test(self, point, expected):
        surf = BOX([0, 0, 0], [2, 0, 0], [0, 1, 0], [0, 0, 0.5])
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "center, dirx, diry, dirz, ans",
        [
            ([0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2], 0),
            ([-2, -2, -2], [4, 0, 0], [0, 4, 0], [0, 0, 4], -1),
            ([-3, -3, -3], [1, 0, 0], [0, 1, 0], [0, 0, 1], +1),
        ],
    )
    def test_box_test(self, box, center, dirx, diry, dirz, ans):
        surf = BOX(center, dirx, diry, dirz)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize(
        "center, dirx, diry, dirz",
        [
            ([0, 0, 1], [2, 0, 0], [0, 3, 0], [0, 0, 4]),
            ([1, 0, 0], [-2, 0, 0], [0, 3, 0], [0, 0, -4]),
            ([0, 1, 0], [10, 0, 0], [0, -5, 0], [0, 0, -6]),
        ],
    )
    def test_transform(self, transform, center, dirx, diry, dirz):
        surf = BOX(center, dirx, diry, dirz)
        c = transform.apply2point(center)
        dx = transform.apply2vector(dirx)
        dy = transform.apply2vector(diry)
        dz = transform.apply2vector(dirz)

        surf_tr = surf.transform(transform)
        ac, adx, ady, adz = surf_tr.get_params()
        np.testing.assert_array_almost_equal(c, ac)
        np.testing.assert_array_almost_equal(dx, adx)
        np.testing.assert_array_almost_equal(dy, ady)
        np.testing.assert_array_almost_equal(dz, adz)

    @pytest.mark.parametrize(
        "center, dirx, diry, dirz, options",
        [
            ([0, 0, 1], [2, 0, 0], [0, 3, 0], [0, 0, 4], {}),
            ([1, 0, 0], [-2, 0, 0], [0, 3, 0], [0, 0, -4], {"name": 3}),
            (
                [0, 1, 0],
                [10, 0, 0],
                [0, -5, 0],
                [0, 0, -6],
                {"name": 4, "comments": ["abc", "def"]},
            ),
        ],
    )
    def test_pickle(self, center, dirx, diry, dirz, options):
        surf = BOX(center, dirx, diry, dirz, **options)
        surf_un = pass_through_pickle(surf)
        ac, adx, ady, adz = surf_un.get_params()
        np.testing.assert_array_almost_equal(center, ac)
        np.testing.assert_array_almost_equal(dirx, adx)
        np.testing.assert_array_almost_equal(diry, ady)
        np.testing.assert_array_almost_equal(dirz, adz)
        assert surf.options == surf_un.options

    surfs: Final = [
        create_surface("RPP", -1, 1, -2, 2, -3, 3, name=1),  # 0
        create_surface("BOX", -1, -2, -3, 2, 0, 0, 0, 4, 0, 0, 0, 6, name=1),  # 1
        create_surface("BOX", 1, 2, 3, -2, 0, 0, 0, -4, 0, 0, 0, -6, name=2),  # 2
        create_surface("RPP", -2, 1, -2, 2, -3, 3, name=1),  # 3
        create_surface("BOX", -2, -2, -3, 3, 0, 0, 0, 4, 0, 0, 0, 6, name=1),  # 4
        create_surface("BOX", 1, 2, 3, -3, 0, 0, 0, -4, 0, 0, 0, -6, name=2),  # 5
    ]

    eq_matrix: Final = [
        [1, 1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_eq(self, i1, s1, i2, s2):
        result = s1 == s2
        assert result == bool(self.eq_matrix[i1][i2])

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            assert hash(s1) == hash(s2)

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 BOX -1 -2 -3 2 0 0 0 4 0 0 0 6 ",
                "1 BOX -1 -2 -3 2 0 0 0 4 0 0 0 6 ",
                "2 BOX 1 2 3 -2 0 0 0 -4 0 0 0 -6 ",
                "1 BOX -2 -2 -3 3 0 0 0 4 0 0 0 6 ",
                "1 BOX -2 -2 -3 3 0 0 0 4 0 0 0 6 ",
                "2 BOX 1 2 3 -3 0 0 0 -4 0 0 0 -6 ",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr(True)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, number, norm, k",
        [
            (surfs[0], 1, [1, 0, 0], -1.0),
            (surfs[0], 2, [-1, 0, 0], -1.0),
            (surfs[0], 3, [0, 1, 0], -2.0),
            (surfs[0], 4, [0, -1, 0], -2.0),
            (surfs[0], 5, [0, 0, 1], -3.0),
            (surfs[0], 6, [0, 0, -1], -3.0),
        ],
    )
    def test_surface(self, surface, number, norm, k):
        s = surface.surface(number)
        np.testing.assert_almost_equal(k, s._k)
        np.testing.assert_array_almost_equal(norm, s._v)


class TestRCC:
    @pytest.mark.parametrize(
        "center, axis, radius",
        [
            ([0, 0, 1], [0, 0, 2], 3),
            ([1, 0, 0], [-2, 0, 0], 1),
            ([0, -1, 0], [10, 0, 0], 1),
        ],
    )
    def test_init(self, transform, center, axis, radius):
        surf = RCC(center, axis, radius, transform=transform)
        c = transform.apply2point(center)
        a = transform.apply2vector(axis)
        ac, axc, rc = surf.get_params()
        np.testing.assert_array_almost_equal(c, ac)
        np.testing.assert_array_almost_equal(a, axc)
        np.testing.assert_almost_equal(radius, rc)

    @pytest.mark.parametrize(
        "point, expected",
        [
            ([0, 0, 0], -1),
            ([1, 0, -0.99], -1),
            ([1, 0, -1.01], +1),
            ([1, 0, 0.99], -1),
            ([1, 0, 1.01], +1),
            ([2.99, 0, 0], -1),
            ([4.01, 0, 0], +1),
            ([3.99, 0, 0], -1),
            ([-2.01, 0, 0], +1),
            ([-1.99, 0, 0], -1),
            ([-1.99, 0, -0.99], -1),
            ([-1.99, 0, 0.99], -1),
            ([-2.01, 0, -0.99], +1),
            ([-2.01, 0, 0.99], +1),
            ([-1.99, 0, -1.01], +1),
            ([-1.99, 0, 1.01], +1),
            ([-1.12, -2.12, 0], -1),
            ([-1.13, -2.13, 0], +1),
        ],
    )
    def test_point_test(self, point, expected):
        surf = RCC([1, 0, -1], [0, 0, 2], 3)
        result = surf.test_points(point)
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "center, axis, rad, ans",
        [
            # pytest.param(
            #     [-2, 0, 0],
            #     [4, 0, 0],
            #     0.5,
            #     0,
            #     marks=pytest.mark.skipif(
            #         sys.platform == "darwin"
            #         or sys.platform == "linux"
            #         and sys.version_info[0:2] < (3, 9),
            #         reason="Fails on MacOS and Linux with python 3.8",
            #     ),
            # ),
            ([-2, 0, 0], [4, 0, 0], 3, -1),
            pytest.param(
                [-0.75, 0, 0],
                [1.5, 0, 0],
                0.75,
                0,
                marks=pytest.mark.skip(
                    reason="Fails on MacOS and occasionally on Linux and Windows",
                ),
            ),
            ([-2, 6, 0], [4, 0, 0], 3, +1),
        ],
    )
    def test_box_test(self, box, center, axis, rad, ans):
        surf = RCC(center, axis, rad)
        assert surf.test_box(box) == ans

    @pytest.mark.parametrize(
        "center, axis, radius",
        [
            ([0, 0, 1], [0, 0, 2], 3),
            ([1, 0, 0], [-2, 0, 0], 1),
            ([0, -1, 0], [10, 0, 0], 1),
        ],
    )
    def test_transform(self, transform, center, axis, radius):
        surf = RCC(center, axis, radius)
        c = transform.apply2point(center)
        a = transform.apply2vector(axis)

        surf_tr = surf.transform(transform)
        ac, ax, r = surf_tr.get_params()
        np.testing.assert_array_almost_equal(c, ac)
        np.testing.assert_array_almost_equal(a, ax)
        np.testing.assert_almost_equal(radius, r)

    @pytest.mark.parametrize(
        "center, axis, radius, options",
        [
            ([0, 0, 1], [0, 0, 2], 3, {}),
            ([1, 0, 0], [-2, 0, 0], 1, {"name": 3}),
            ([0, -1, 0], [10, 0, 0], 1, {"name": 4, "comments": ["abc", "def"]}),
        ],
    )
    def test_pickle(self, center, axis, radius, options):
        surf = RCC(center, axis, radius, **options)
        surf_un = pass_through_pickle(surf)
        ac, ax, r = surf_un.get_params()
        np.testing.assert_array_almost_equal(center, ac)
        np.testing.assert_array_almost_equal(axis, ax)
        np.testing.assert_almost_equal(radius, r)
        assert surf.options == surf_un.options

    surfs: Final = [
        create_surface("RCC", -1, 1, -2, 2, 0, 0, 4, name=1),  # 0
        create_surface("RCC", -1, 1, -2, 2, 0, 0, 4, name=1),  # 1
        create_surface("RCC", -1, 2, -2, 2, 0, 0, 4, name=2),  # 2
        create_surface("RCC", 1, 2, -2, -2, 0, 0, 4, name=1),  # 3
        create_surface("RCC", -1, 1, -2, 2, 0, 0, 3, name=1),  # 4
        create_surface("RCC", 1, 1, -2, -2, 0, 0, 3, name=2),  # 5
    ]

    eq_matrix: Final = [
        [1, 1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_eq(self, i1, s1, i2, s2):
        result = s1 == s2
        assert result == bool(self.eq_matrix[i1][i2])

    @pytest.mark.parametrize("i1, s1", enumerate(surfs))
    @pytest.mark.parametrize("i2, s2", enumerate(surfs))
    def test_hash(self, i1, s1, i2, s2):
        if self.eq_matrix[i1][i2]:
            assert hash(s1) == hash(s2)

    @pytest.mark.parametrize(
        "surface, answer",
        zip(
            surfs,
            [
                "1 RCC -1 1 -2 2 0 0 4 ",
                "1 RCC -1 1 -2 2 0 0 4 ",
                "2 RCC -1 2 -2 2 0 0 4 ",
                "1 RCC 1 2 -2 -2 0 0 4 ",
                "1 RCC -1 1 -2 2 0 0 3 ",
                "2 RCC 1 1 -2 -2 0 0 3 ",
            ],
            strict=False,
        ),
    )
    def test_mcnp_repr(self, surface, answer):
        desc = surface.mcnp_repr(True)
        assert desc == answer

    @pytest.mark.parametrize(
        "surface, number, norm, k",
        [(surfs[0], 2, [1, 0, 0], -1.0), (surfs[0], 3, [-1, 0, 0], -1.0)],
    )
    def test_surface(self, surface, number, norm, k):
        s = surface.surface(number)
        np.testing.assert_almost_equal(k, s._k)
        np.testing.assert_array_almost_equal(norm, s._v)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (
            create_surface("PX", 0),
            create_surface("PX", 1e-12),
            True,
        ),
        (
            create_surface("PX", 0).transform(Transformation(translation=[0, 0, 0])),
            create_surface("PX", 0).transform(Transformation(translation=[0, 0, 1e-12])),
            True,
        ),
        (
            create_surface("PX", 0),
            create_surface("PX", 1e-11),
            False,
        ),
        (
            create_surface("PX", 0).transform(Transformation(translation=[0, 0, 0])),
            create_surface("PX", 0).transform(Transformation(translation=[1e-11, 0, 0])),
            False,
        ),
    ],
)
def test_plane_is_close(a: Plane, b: Plane, expected: bool) -> None:
    assert a.is_close_to(b) == expected
    assert b.is_close_to(a) == expected
