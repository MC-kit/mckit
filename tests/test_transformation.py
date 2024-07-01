from __future__ import annotations

import numpy as np
import pytest

from mckit.geometry import ORIGIN
from mckit.transformation import IDENTITY_ROTATION, Transformation


@pytest.mark.parametrize(
    "args, rot, offset, options",
    [
        ({}, IDENTITY_ROTATION, ORIGIN, {}),
        ({"indegrees": True}, IDENTITY_ROTATION, ORIGIN, {}),
        ({"indegrees": False}, IDENTITY_ROTATION, ORIGIN, {}),
        ({"inverted": True}, IDENTITY_ROTATION, ORIGIN, {}),
        ({"inverted": False}, IDENTITY_ROTATION, ORIGIN, {}),
        ({"translation": [1, 0, 0]}, IDENTITY_ROTATION, np.array([1, 0, 0]), {}),
        (
            {"translation": [1, 0, 0], "inverted": True},
            IDENTITY_ROTATION,
            np.array([-1, 0, 0]),
            {},
        ),
        (
            {"translation": [1, 2, 3], "inverted": True},
            IDENTITY_ROTATION,
            np.array([-1, -2, -3]),
            {},
        ),
        (
            {"translation": [1, 2, 3], "inverted": True, "name": 1},
            IDENTITY_ROTATION,
            np.array([-1, -2, -3]),
            {"name": 1},
        ),
        (
            {"rotation": np.cos(np.array([30, 60, 90, 120, 30, 90, 90, 90, 0]) * np.pi / 180)},
            np.cos(np.array([[30, 120, 90], [60, 30, 90], [90, 90, 0]]) * np.pi / 180),
            ORIGIN,
            {},
        ),
        (
            {"rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
            np.cos(np.array([[30, 120, 90], [60, 30, 90], [90, 90, 0]]) * np.pi / 180),
            ORIGIN,
            {},
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
            },
            np.cos(np.array([[30, 120, 90], [60, 30, 90], [90, 90, 0]]) * np.pi / 180),
            np.array([1, 2, 3]),
            {},
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
                "inverted": True,
            },
            np.cos(np.array([[30, 120, 90], [60, 30, 90], [90, 90, 0]]) * np.pi / 180),
            np.array([-(np.sqrt(3) - 2) / 2, -(2 * np.sqrt(3) + 1) / 2, -3]),
            {},
        ),
    ],
)
def test_creation(args, rot, offset, options):
    tr = Transformation(**args)
    np.testing.assert_array_almost_equal(tr._u, rot)
    np.testing.assert_array_almost_equal(tr._t, offset)
    for k, v in options.items():
        assert tr[k] == v


@pytest.mark.parametrize(
    "args",
    [
        {"translation": [0]},
        {"translation": [0, 1]},
        {"translation": [0, 1, 2, 3]},
        {"translation": [0, 1, 2, 3, 4]},
        {"rotation": [0, 1, 2]},
        {"rotation": [1, 2, 3, 4, 5, 6, 7, 8]},
        {"rotation": [30.058, 59.942, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [29.942, 60.058, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [30, 60, 90, 120.058, 30.058, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [30, 60, 90, 119.942, 29.942, 90, 90, 90, 0], "indegrees": True},
        {
            "rotation": [30, 60, 90, 120, 30, 90, 90.058, 90.058, 0.058],
            "indegrees": True,
        },
        {
            "rotation": [30, 60, 90, 120, 30, 90, 89.942, 89.942, 0.058],
            "indegrees": True,
        },
    ],
)
def test_creation_failure(args):
    with pytest.raises(ValueError, match="wrong|is greater"):
        Transformation(**args)


@pytest.mark.parametrize(
    "args, answer",
    [
        (
            {"rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
            [0, 0, 0, 30, 60, 90, 120, 30, 90, 90, 90, 0],
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
            },
            [1, 2, 3, 30, 60, 90, 120, 30, 90, 90, 90, 0],
        ),
    ],
)
def test_words(args, answer):
    tr = Transformation(**args)
    words = [float(w) for w in "".join(tr.get_words()).split()]
    np.testing.assert_array_almost_equal(words, answer)


@pytest.mark.parametrize(
    "args, options, answer",
    [
        (
            {"rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
            {},
            None,
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
            },
            {"name": 1},
            1,
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
            },
            {"name": 2},
            2,
        ),
        (
            {
                "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
                "indegrees": True,
                "translation": [1, 2, 3],
            },
            {"name": 3},
            3,
        ),
    ],
)
def test_name(args, options, answer):
    tr = Transformation(**args, **options)
    assert tr.name() == answer


@pytest.mark.parametrize(
    "args",
    [
        {"rotation": [30.057, 59.943, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [29.943, 60.057, 90, 120, 30, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [30, 60, 90, 120.057, 30.057, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [30, 60, 90, 119.943, 29.943, 90, 90, 90, 0], "indegrees": True},
        {"rotation": [30, 60, 90, 120, 30, 90, 90.057, 90, 0.057], "indegrees": True},
        {"rotation": [30, 60, 90, 120, 30, 90, 89.943, 90, 0.057], "indegrees": True},
    ],
)
def test_orthogonalization(args):
    tr = Transformation(**args)
    result = np.dot(tr._u.transpose(), tr._u)
    np.testing.assert_array_almost_equal(result, IDENTITY_ROTATION)


@pytest.fixture(scope="module")
def transforms():
    return Transformation(
        translation=[1, 2, -3],
        indegrees=True,
        rotation=[30, 60, 90, 120, 30, 90, 90, 90, 0],
    )


@pytest.mark.parametrize(
    "points, expected",
    [
        (np.array([1, 0, 0]), np.array([np.sqrt(3) / 2 + 1, 2.5, -3])),
        (np.array([2, 0, 0]), np.array([np.sqrt(3) + 1, 3, -3])),
        (np.array([0, 1, 0]), np.array([0.5, np.sqrt(3) / 2 + 2, -3])),
        (np.array([0, 2, 0]), np.array([0, np.sqrt(3) + 2, -3])),
        (np.array([0, 0, 1]), np.array([1, 2, -2])),
        (
            np.array([[1, 0, 0], [2, 0, 0], [0, 1, 0], [0, 2, 0], [0, 0, 1]]),
            np.array(
                [
                    [np.sqrt(3) / 2 + 1, 2.5, -3],
                    [np.sqrt(3) + 1, 3, -3],
                    [0.5, np.sqrt(3) / 2 + 2, -3],
                    [0, np.sqrt(3) + 2, -3],
                    [1, 2, -2],
                ]
            ),
        ),
    ],
)
def test_point_transformation(transforms, points, expected):
    result = transforms.apply2point(points)
    np.testing.assert_array_almost_equal(result, expected)


@pytest.mark.parametrize(
    "vectors, expected",
    [
        (np.array([1, 0, 0]), np.array([np.sqrt(3) / 2, 0.5, 0])),
        (np.array([2, 0, 0]), np.array([np.sqrt(3), 1, 0])),
        (np.array([0, 1, 0]), np.array([-0.5, np.sqrt(3) / 2, 0])),
        (np.array([0, 2, 0]), np.array([-1, np.sqrt(3), 0])),
        (np.array([0, 0, 1]), np.array([0, 0, 1])),
        (
            np.array([[1, 0, 0], [2, 0, 0], [0, 1, 0], [0, 2, 0], [0, 0, 1]]),
            np.array(
                [
                    [np.sqrt(3) / 2, 0.5, 0],
                    [np.sqrt(3), 1, 0],
                    [-0.5, np.sqrt(3) / 2, 0],
                    [-1, np.sqrt(3), 0],
                    [0, 0, 1],
                ]
            ),
        ),
    ],
)
def test_vector_transformation(transforms, vectors, expected):
    result = transforms.apply2vector(vectors)
    np.testing.assert_array_almost_equal(result, expected)


@pytest.mark.parametrize(
    "norm, point",
    [
        (np.array([1, 0, 0]), np.array([2, 3, 5])),
        (np.array([0, 1, 0]), np.array([2, 3, 5])),
        (np.array([0, 0, 1]), np.array([2, 3, 5])),
        (np.array([1, -2, 3]), np.array([2, 3, 5])),
        (np.array([-4, 0, 5]), np.array([2, 3, 5])),
    ],
)
def test_plane_transformation(transforms, norm, point):
    k1 = -np.dot(norm, point)
    v, k = transforms.apply2plane(norm, k1)
    v_ref = transforms.apply2vector(norm)
    k_ref = -np.dot(v_ref, transforms.apply2point(point))
    np.testing.assert_array_almost_equal(v, v_ref)
    assert k == pytest.approx(k_ref, rel=1.0e-10)


@pytest.mark.parametrize("point, radius", [(np.array([3, -4, 7]), 4)])
def test_gq_transformation(transforms, point, radius):
    m1 = IDENTITY_ROTATION
    v1 = -2 * point
    k1 = np.linalg.norm(point) ** 2 - radius**2
    m, v, k = transforms.apply2gq(m1, v1, k1)
    v_ref = -2 * transforms.apply2point(point)
    k_ref = np.linalg.norm(-0.5 * v_ref) ** 2 - radius**2
    np.testing.assert_array_almost_equal(m, m1)
    np.testing.assert_array_almost_equal(v, v_ref)
    np.testing.assert_array_almost_equal(k, k_ref)


tr_tr_cases = [
    {"translation": [1, 2, 3]},
    {"translation": [-4, 2, -3]},
    {
        "translation": [3, 0, 9],
        "rotation": [30, 60, 90, 120, 30, 90, 90, 90, 0],
        "indegrees": True,
    },
    {
        "translation": [1, 4, -2],
        "rotation": [0, 90, 90, 90, 30, 60, 90, 120, 30],
        "indegrees": True,
    },
    {
        "translation": [-2, 5, 3],
        "rotation": [30, 90, 60, 90, 0, 90, 120, 90, 30],
        "indegrees": True,
    },
]


@pytest.fixture()
def trtr():
    return [Transformation(**tdata) for tdata in tr_tr_cases]


@pytest.mark.parametrize("tr1_no", range(len(tr_tr_cases)))
@pytest.mark.parametrize("tr2_no", range(len(tr_tr_cases)))
@pytest.mark.parametrize(
    "point",
    [
        np.array([1, 0, 0]),
        np.array([2, -3, 1]),
        np.array([-4, 1, 9]),
        np.array([7, 2, 5]),
        np.array([8, -1, 3]),
        np.array([8, -3, 2]),
        np.array([3, 6, 4]),
        np.array([2, -5, -1]),
        np.array([-2, 7, 2]),
    ],
)
def test_apply2tr(trtr, tr1_no, tr2_no, point):
    tr1 = trtr[tr1_no]
    tr2 = trtr[tr2_no]
    ans = tr1.apply2point(tr2.apply2point(point))
    tr = tr1.apply2transform(tr2)
    result = tr.apply2point(point)
    np.testing.assert_array_almost_equal(ans, result)


@pytest.mark.parametrize(
    "p1, p",
    [
        (np.array([1, 0, 0]), np.array([np.sqrt(3) / 2 + 1, 2.5, -3])),
        (np.array([2, 0, 0]), np.array([np.sqrt(3) + 1, 3, -3])),
        (np.array([0, 1, 0]), np.array([0.5, np.sqrt(3) / 2 + 2, -3])),
        (np.array([0, 2, 0]), np.array([0, np.sqrt(3) + 2, -3])),
        (np.array([0, 0, 1]), np.array([1, 2, -2])),
        (
            np.array([[1, 0, 0], [2, 0, 0], [0, 1, 0], [0, 2, 0], [0, 0, 1]]),
            np.array(
                [
                    [np.sqrt(3) / 2 + 1, 2.5, -3],
                    [np.sqrt(3) + 1, 3, -3],
                    [0.5, np.sqrt(3) / 2 + 2, -3],
                    [0, np.sqrt(3) + 2, -3],
                    [1, 2, -2],
                ]
            ),
        ),
    ],
)
def test_reverse(transforms, p1, p):
    tr_inv = transforms.reverse()
    result = tr_inv.apply2point(p)
    np.testing.assert_array_almost_equal(result, p1)


@pytest.mark.parametrize(
    "options", [{"name": 1, "comment": "abcdef"}, {"name": 1}, {"comment": "rrreee"}]
)
@pytest.mark.parametrize("tr_no", range(len(tr_tr_cases)))
def test_set_item(trtr, tr_no, options):
    tr = trtr[tr_no]
    for k, v in options.items():
        tr[k] = v
    for k, v in options.items():
        assert tr[k] == v
