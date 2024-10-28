from __future__ import annotations

from typing import Final

from itertools import product

import numpy as np
import pytest

from mckit import read_meshtal
from mckit.body import Body
from mckit.fmesh import CylMesh, RectMesh
from mckit.geometry import EX, EY, EZ
from mckit.material import Material
from mckit.surface import create_surface
from mckit.transformation import Transformation
from mckit.utils.resource import path_resolver

transforms = [
    None,
    Transformation(translation=[2, -1, 3]),
    Transformation(
        translation=[1, 2, -3],
        indegrees=True,
        rotation=[30, 60, 90, 120, 30, 90, 90, 90, 0],
    ),
    Transformation(
        translation=[1, 0, 0],
        rotation=[90, 0, 90, 180, 90, 90, 90, 90, 0],
        indegrees=True,
    ),
]


bins = [
    {"xbins": [0, 1, 2, 4, 6], "ybins": [0, 2, 5], "zbins": [-1, 1, 3]},
    {"xbins": [2, 4, 6, 8], "ybins": [2, 3], "zbins": [1, 4, 7]},
    {"xbins": [-3, -1, 1], "ybins": [-2, -1, 0, 1], "zbins": [-5, -4, -3]},
]


def create_rmesh(bins, tr):
    return RectMesh(bins["xbins"], bins["ybins"], bins["zbins"], transform=tr)


class TestRectMesh:
    @pytest.mark.parametrize(
        "mi, ti",
        [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 0),
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 0),
            (2, 1),
            (2, 2),
            (2, 3),
        ],
    )
    def test_creation(self, mi: int, ti: int):
        _bin = bins[mi]
        tr = transforms[ti]
        mesh = create_rmesh(_bin, tr)
        np.testing.assert_array_almost_equal(mesh._xbins, _bin["xbins"])
        np.testing.assert_array_almost_equal(mesh._ybins, _bin["ybins"])
        np.testing.assert_array_almost_equal(mesh._zbins, _bin["zbins"])

        origin = [_bin["xbins"][0], _bin["ybins"][0], _bin["zbins"][0]]
        ex = EX
        ey = EY
        ez = EZ
        if tr is not None:
            ex = tr.apply2vector(ex)
            ey = tr.apply2vector(ey)
            ez = tr.apply2vector(ez)
            origin = tr.apply2point(origin)
        np.testing.assert_array_almost_equal(mesh._origin, origin)
        np.testing.assert_array_almost_equal(mesh._ex, ex)
        np.testing.assert_array_almost_equal(mesh._ey, ey)
        np.testing.assert_array_almost_equal(mesh._ez, ez)

    @pytest.mark.parametrize("ti", range(4))
    @pytest.mark.parametrize("mi", range(3))
    def test_bounding_box(self, mi: int, ti: int):
        tr = transforms[ti]
        _bin = bins[mi]
        mesh = create_rmesh(_bin, tr)
        box = mesh.bounding_box()
        corners = box.corners
        ans_corners = [
            [_bin["xbins"][0], _bin["ybins"][0], _bin["zbins"][0]],
            [_bin["xbins"][0], _bin["ybins"][0], _bin["zbins"][-1]],
            [_bin["xbins"][0], _bin["ybins"][-1], _bin["zbins"][0]],
            [_bin["xbins"][0], _bin["ybins"][-1], _bin["zbins"][-1]],
            [_bin["xbins"][-1], _bin["ybins"][0], _bin["zbins"][0]],
            [_bin["xbins"][-1], _bin["ybins"][0], _bin["zbins"][-1]],
            [_bin["xbins"][-1], _bin["ybins"][-1], _bin["zbins"][0]],
            [_bin["xbins"][-1], _bin["ybins"][-1], _bin["zbins"][-1]],
        ]
        if tr:
            ans_corners = tr.apply2point(ans_corners)
        np.testing.assert_array_almost_equal(corners, ans_corners)

    @pytest.mark.parametrize(
        "mi, ti, ans",
        [
            (0, 0, (4, 2, 2)),
            (0, 1, (4, 2, 2)),
            (0, 2, (4, 2, 2)),
            (0, 3, (4, 2, 2)),
            (1, 0, (3, 1, 2)),
            (1, 1, (3, 1, 2)),
            (1, 2, (3, 1, 2)),
            (1, 3, (3, 1, 2)),
            (2, 0, (2, 3, 2)),
            (2, 1, (2, 3, 2)),
            (2, 2, (2, 3, 2)),
            (2, 3, (2, 3, 2)),
        ],
    )
    def test_shape(self, mi, ti, ans):
        mesh = create_rmesh(bins[mi], transforms[ti])
        assert mesh.shape == ans

    surfaces: Final = {
        1: create_surface("PY", 3.5),
        2: create_surface("PY", -1.0),
        3: create_surface("PX", 3.0),
        4: create_surface("PX", 1.5),
        5: create_surface("PZ", 2.0),
        6: create_surface("PZ", -2.0),
        7: create_surface("PX", 5.0),
    }

    # noinspection PyTypeChecker
    bodies: Final = [
        Body(
            [
                surfaces[1],
                "C",
                surfaces[2],
                "I",
                surfaces[3],
                "C",
                "I",
                surfaces[4],
                "I",
                surfaces[5],
                "C",
                "I",
                surfaces[6],
                "I",
            ],
            name=1,
            MAT=Material(atomic=[("Fe", 1)], density=7.8),
        ),
        Body(
            [
                surfaces[1],
                "C",
                surfaces[2],
                "I",
                surfaces[7],
                "C",
                "I",
                surfaces[3],
                "I",
                surfaces[5],
                "C",
                "I",
                surfaces[6],
                "I",
            ],
            name=2,
            MAT=Material(atomic=[("C", 1)], density=2.7),
        ),
        Body(
            [
                surfaces[1],
                surfaces[2],
                "C",
                "U",
                surfaces[4],
                "C",
                "U",
                surfaces[7],
                "U",
                surfaces[5],
                "U",
                surfaces[6],
                "C",
                "U",
            ],
            name=3,
        ),
    ]

    @pytest.mark.parametrize("mi, ti", product(range(len(bins)), range(len(transforms))))
    def test_get_voxel(self, mi: int, ti: int):
        tr = transforms[ti]
        _bin = bins[mi]
        mesh = create_rmesh(_bin, tr)
        shape = mesh.shape
        for i, j, k in product(range(shape[0]), range(shape[1]), range(shape[2])):
            vox = mesh.get_voxel(i, j, k)
            corners = [
                list(pr)
                for pr in product(
                    _bin["xbins"][i : i + 2],
                    _bin["ybins"][j : j + 2],
                    _bin["zbins"][k : k + 2],
                )
            ]
            if tr is not None:
                corners = tr.apply2point(corners)
            np.testing.assert_array_almost_equal(vox.corners, corners)

    points: Final = [
        [0.5, 0.9, 0],
        [-1.4, 0.5, 0.1],
        [3, 2.5, 1.9],
        [0.5, 0.1, -0.3],
        [-1.8, -1.5, -3.5],
        [-0.1, 0.4, -4.1],
        [5.1, 4.9, 1.4],
        [
            [0.5, 0.9, 0],
            [-1.4, 0.5, 0.1],
            [3, 2.5, 1.9],
            [0.5, 0.1, -0.3],
            [-1.8, -1.5, -3.5],
            [-0.1, 0.4, -4.1],
            [5.1, 4.9, 1.4],
        ],
    ]

    @pytest.mark.parametrize(
        "mi, ti, pi, local",
        product(range(len(bins)), range(len(transforms)), range(len(points)), [False, True]),
    )
    def test_voxel_index(self, mi: int, ti: int, pi: int, local: bool):
        tr = transforms[ti]
        _bin = bins[mi]
        mesh = create_rmesh(_bin, tr)
        pt = self.points[pi]
        result = mesh.voxel_index(pt, local=local)
        if local is False and tr is not None:
            pt = tr.reverse().apply2point(pt)

        def check_one(r, pt):
            if r is not None:
                i, j, k = r
                assert _bin["xbins"][i] <= pt[0] <= _bin["xbins"][i + 1]
                assert _bin["ybins"][j] <= pt[1] <= _bin["ybins"][j + 1]
                assert _bin["zbins"][k] <= pt[2] <= _bin["zbins"][k + 1]
            else:
                px = pt[0] <= _bin["xbins"][0] or pt[0] >= _bin["xbins"][-1]
                py = pt[1] <= _bin["ybins"][0] or pt[1] >= _bin["ybins"][-1]
                pz = pt[2] <= _bin["zbins"][0] or pt[2] >= _bin["zbins"][-1]
                assert px or py or pz

        if np.array(pt).shape == (3,):
            check_one(result, pt)
        else:
            for r, p in zip(result, pt, strict=False):
                check_one(r, p)

    @pytest.mark.parametrize(
        "mi, index, answer",
        [
            (0, (3, 1, 0), (3, 1, 0)),
            (0, (0, 0, 0), (0, 0, 0)),
            (0, (-1, 0, 0), None),
            (0, (0, -1, 0), None),
            (0, (0, 0, -1), None),
            (0, (4, 1, 1), None),
            (0, (3, 2, 1), None),
            (0, (3, 1, 2), None),
            (1, (2, 0, 1), (2, 0, 1)),
            (1, (2, 1, 2), None),
            (2, (1, 2, 1), (1, 2, 1)),
            (2, (1, 3, 1), None),
            (2, (10, 10, 10), None),
            (2, (10, -10, 10), None),
        ],
    )
    def test_check_indices(self, mi, index, answer):
        mesh = create_rmesh(bins[mi], None)
        check = mesh.check_indices(*index)
        assert check == answer

    @pytest.mark.parametrize("ti", range(len(transforms)))
    @pytest.mark.parametrize(
        "mi, args, expected",
        [
            (0, {}, None),
            (0, {"X": 0.5}, {"axis": 0, "index": 0, "x": [1.0, 3.5], "y": [0.0, 2.0]}),
            (
                0,
                {"Y": 0.5},
                {"axis": 1, "index": 0, "x": [0.5, 1.5, 3.0, 5.0], "y": [0.0, 2.0]},
            ),
            (
                0,
                {"Z": 0.5},
                {"axis": 2, "index": 0, "x": [0.5, 1.5, 3.0, 5.0], "y": [1.0, 3.5]},
            ),
            (0, {"X": -1}, None),
            (1, {"Y": 10}, None),
            (2, {"Z": -100}, None),
            (0, {"X": 0.5, "Y": 0.5, "Z": 0.5}, None),
            (1, {"X": 0, "Y": 2.5}, None),
            (1, {"X": 3, "Y": 0}, None),
            (1, {"X": 3, "Z": 9}, None),
            (2, {"X": -2, "Y": 0.5}, None),
            (
                1,
                {"Y": 2.9},
                {"axis": 1, "index": 0, "x": [3.0, 5.0, 7.0], "y": [2.5, 5.5]},
            ),
            (1, {"Z": 4.9}, {"axis": 2, "index": 1, "x": [3.0, 5.0, 7.0], "y": [2.5]}),
            (
                2,
                {"X": 0.0},
                {"axis": 0, "index": 1, "x": [-1.5, -0.5, 0.5], "y": [-4.5, -3.5]},
            ),
            (
                2,
                {"Z": -4.1},
                {"axis": 2, "index": 0, "x": [-2.0, 0.0], "y": [-1.5, -0.5, 0.5]},
            ),
            (0, {"X": 5}, {"axis": 0, "index": 3, "x": [1.0, 3.5], "y": [0.0, 2.0]}),
        ],
    )
    def test_slice_index(self, ti: int, mi: int, args, expected):
        tr = transforms[ti]
        _bin = bins[mi]
        mesh = create_rmesh(_bin, tr)
        if expected is None:
            with pytest.raises(
                ValueError,
                match="Wrong number of fixed spatial variables|Specified point lies outside of the mesh",
            ):
                mesh.slice_axis_index(**args)
        else:
            axis, index, x, y = mesh.slice_axis_index(**args)
            assert axis == expected["axis"]
            assert index == expected["index"]
            np.testing.assert_array_almost_equal(x, expected["x"])
            np.testing.assert_array_almost_equal(y, expected["y"])


parser_test_data = path_resolver("tests")
# dvp: On Linux access to package should be organized with resource name resolver.


class TestFMesh:
    @pytest.fixture
    def tallies(self):
        file_name = parser_test_data("parser_test_data/fmesh.m")
        return read_meshtal(file_name)

    @pytest.mark.parametrize(
        "name, particle, histories, meshclass",
        [
            (14, "NEUTRON", 10000000, RectMesh),
            (24, "PHOTON", 10000000, CylMesh),
            (34, "ELECTRON", 10000000, RectMesh),
            (44, "NEUTRON", 10000000, CylMesh),
            (54, "NEUTRON", 10000000, CylMesh),
            (64, "ELECTRON", 10000000, RectMesh),
            (74, "NEUTRON", 10000000, RectMesh),
        ],
    )
    def test_creation(self, tallies, name, particle, histories, meshclass):
        assert tallies[name]._name == name
        assert tallies[name].particle == particle
        assert tallies[name].histories == histories
        assert tallies[name].mesh.__class__ == meshclass

    @pytest.mark.parametrize(
        "name, E, _dir, value, x_ans, y_ans, data_ans, max_err",
        [
            (
                34,
                "total",
                "X",
                0.5,
                np.array([-2.0, 0.0, 2.0, 4.0]),
                np.array([-2.80, -0.40, 2.00, 4.40, 6.80]),
                np.array(
                    [
                        [
                            2.93786841e-05,
                            1.70248000e-05,
                            1.00628000e-05,
                            5.66025000e-06,
                            3.11381000e-06,
                        ],
                        [
                            4.14040051e-05,
                            2.01139793e-05,
                            1.08131089e-05,
                            6.11828000e-06,
                            3.37041000e-06,
                        ],
                        [
                            2.85912544e-05,
                            1.71446000e-05,
                            9.64213000e-06,
                            5.34389205e-06,
                            3.04467000e-06,
                        ],
                        [
                            1.38793682e-05,
                            1.14846718e-05,
                            6.76504699e-06,
                            4.63210922e-06,
                            2.49310000e-06,
                        ],
                    ]
                ),
                np.array(
                    [
                        [1.0, 0.02122, 0.02782, 0.03681, 0.04955],
                        [0.82592, 1.0, 1.0, 0.03578, 0.04802],
                        [1.0, 0.02122, 0.02836, 1.0, 0.04925],
                        [0.93217, 1.0, 1.0, 1.0, 0.0549901],
                    ]
                ),
            ),
            (
                34,
                "total",
                "Y",
                2.5,
                np.array([-2.00, -0.00, 2.00]),
                np.array([-2.80, -0.40, 2.00, 4.40, 6.80]),
                np.array(
                    [
                        [
                            2.20697440e-05,
                            1.51039385e-05,
                            8.60972000e-06,
                            5.05476000e-06,
                            3.02462000e-06,
                        ],
                        [
                            2.85912544e-05,
                            1.71446000e-05,
                            9.64213000e-06,
                            5.34389205e-06,
                            3.04467000e-06,
                        ],
                        [
                            2.15657907e-05,
                            1.44082497e-05,
                            8.53781902e-06,
                            5.07401000e-06,
                            2.83177000e-06,
                        ],
                    ]
                ),
                np.array(
                    [
                        [1.0, 1.0, 0.0302, 0.03915, 0.05082],
                        [1.0, 0.02122, 0.02836, 1.0, 0.04925],
                        [1.0, 1.0, 1.0, 0.03899, 0.05175],
                    ]
                ),
            ),
            (
                34,
                "total",
                "Z",
                4.5,
                np.array([-2.00, -0.00, 2.00]),
                np.array([-2.0, 0.0, 2.0, 4.0]),
                np.array(
                    [
                        [
                            5.31042000e-06,
                            5.45955000e-06,
                            5.05476000e-06,
                            3.73063990e-06,
                        ],
                        [
                            5.66025000e-06,
                            6.11828000e-06,
                            5.34389205e-06,
                            4.63210922e-06,
                        ],
                        [
                            5.04945000e-06,
                            5.69297000e-06,
                            5.07401000e-06,
                            3.52305000e-06,
                        ],
                    ]
                ),
                np.array(
                    [
                        [0.03851, 0.0375, 0.03915, 1.0],
                        [0.03681, 0.03578, 1.0, 1.0],
                        [0.03881, 0.03607, 0.03899, 0.04945],
                    ]
                ),
            ),
            (
                34,
                2.0,
                "X",
                0.5,
                np.array([-2.0, 0.0, 2.0, 4.0]),
                np.array([-2.80, -0.40, 2.00, 4.40, 6.80]),
                np.array(
                    [
                        [
                            2.93677000e-05,
                            1.70248000e-05,
                            1.00628000e-05,
                            5.66025000e-06,
                            3.11381000e-06,
                        ],
                        [
                            4.13888000e-05,
                            2.01021000e-05,
                            1.08080000e-05,
                            6.11828000e-06,
                            3.37041000e-06,
                        ],
                        [
                            2.85739000e-05,
                            1.71446000e-05,
                            9.64213000e-06,
                            5.33722000e-06,
                            3.04467000e-06,
                        ],
                        [
                            1.38698000e-05,
                            1.14807000e-05,
                            6.74720000e-06,
                            4.62259000e-06,
                            2.49310000e-06,
                        ],
                    ]
                ),
                np.array(
                    [
                        [0.01637, 0.02122, 0.02782, 0.03681, 0.04955],
                        [0.0139, 0.0196, 0.02668, 0.03578, 0.04802],
                        [0.01662, 0.02122, 0.02836, 0.03747, 0.04925],
                        [0.0238, 0.02623, 0.03377, 0.04113, 0.05499],
                    ]
                ),
            ),
            (
                34,
                10,
                "Y",
                2.5,
                np.array([-2.00, -0.00, 2.00]),
                np.array([-2.80, -0.40, 2.00, 4.40, 6.80]),
                np.array(
                    [
                        [
                            7.96285000e-09,
                            9.83845000e-09,
                            0.00000000e00,
                            0.00000000e00,
                            0.00000000e00,
                        ],
                        [
                            1.26318000e-08,
                            0.00000000e00,
                            0.00000000e00,
                            6.67205000e-09,
                            0.00000000e00,
                        ],
                        [
                            8.21988000e-09,
                            2.23643000e-08,
                            0.00000000e00,
                            0.00000000e00,
                            0.00000000e00,
                        ],
                    ]
                ),
                np.array(
                    [
                        [1.0, 1.0, 0.0, 0.0, 0.0],
                        [0.70981, 0.0, 0.0, 1.0, 0.0],
                        [0.77883, 0.76382, 0.0, 0.0, 0.0],
                    ]
                ),
            ),
            (
                34,
                15,
                "Z",
                4.5,
                np.array([-2.00, -0.00, 2.00]),
                np.array([-2.0, 0.0, 2.0, 4.0]),
                np.array(
                    [
                        [0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00],
                        [0.00000000e00, 0.00000000e00, 0.00000000e00, 8.32928000e-09],
                        [0.00000000e00, 0.00000000e00, 0.00000000e00, 0.00000000e00],
                    ]
                ),
                np.array([[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0]]),
            ),
        ],
    )
    def test_slice(self, tallies, name, E, _dir, value, x_ans, y_ans, data_ans, max_err):
        x, y, data, err = tallies[name].get_slice(E=E, **{_dir: value})
        np.testing.assert_array_almost_equal(x, x_ans)
        np.testing.assert_array_almost_equal(y, y_ans)
        np.testing.assert_array_almost_equal(data, data_ans)
        if E == "total":
            assert np.all(err <= max_err)
        else:
            np.testing.assert_array_almost_equal(err, max_err)

    @pytest.mark.parametrize(
        "name, point, ebins, flux, err",
        [
            (14, (-5, 0, 0), None, None, None),
            (
                14,
                (0.5, 2.4, 4.08),
                np.array([0.00e00, 1.00e36]),
                np.array([8.30197e-04]),
                np.array([0.00517]),
            ),
            (34, (2.1, 6.1, -3.0), None, None, None),
            (34, (2.1, 0.0, -5.1), None, None, None),
            (
                34,
                (0.3, 4.1, 3.6),
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([4.62259e-06, 1.18994e-09, 8.32928e-09]),
                np.array([0.04113, 1.00000, 1.00000]),
            ),
            (
                34,
                (-0.5, 4.9, 5.5),
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([4.62259e-06, 1.18994e-09, 8.32928e-09]),
                np.array([0.04113, 1.00000, 1.00000]),
            ),
            # TODO: Add tests for cylindrical mesh.
        ],
    )
    def test_spectrum(self, tallies, name, point, ebins, flux, err):
        if ebins is None:
            with pytest.raises(ValueError, match="lies outside of the mesh"):
                tallies[name].get_spectrum(point)
        else:
            eb, fl, er = tallies[name].get_spectrum(point)
            assert np.all(eb == ebins)
            assert np.all(fl == flux)
            assert np.all(er == err)

    @pytest.mark.parametrize(
        "name, index, ebins, flux, err",
        [
            (14, (5, 0, 1), None, None, None),
            (24, (0, -7, 4), None, None, None),
            (34, (2, 4, 1), None, None, None),
            (
                14,
                (1, 2, 3),
                np.array([0.00e00, 1.00e36]),
                np.array([8.30197e-04]),
                np.array([0.00517]),
            ),
            (
                24,
                (0, 2, 1),
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([3.21725e-04, 2.64984e-08, 1.83093e-07]),
                np.array([1.80477e-02, 1.00000e00, 7.34192e-01]),
            ),
            (
                34,
                (1, 3, 3),
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([4.62259e-06, 1.18994e-09, 8.32928e-09]),
                np.array([0.04113, 1.00000, 1.00000]),
            ),
        ],
    )
    def test_spectrum_by_index(self, tallies, name, index, ebins, flux, err):
        if ebins is None:
            with pytest.raises(IndexError):
                tallies[name].get_spectrum_by_index(index)
        else:
            eb, fl, er = tallies[name].get_spectrum_by_index(index)
            assert np.all(eb == ebins)
            assert np.all(fl == flux)
            assert np.all(er == err)

    @pytest.mark.parametrize(
        "name, ebins, expected",
        [
            (14, np.array([0.00e00, 1.00e36]), np.array([0.0028638])),
            (
                24,
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([2.86894785e-04, 1.20659945e-08, 1.17386470e-07]),
            ),
            (
                34,
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([1.09034495e-05, 2.91653267e-09, 1.23216448e-09]),
            ),
            (
                44,
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([0.0004493, 0.00038024, 0.00218942]),
            ),
            (
                54,
                np.array([0.00e00, 6.67e00, 1.33e01, 2.00e01]),
                np.array([0.0004493, 0.00038024, 0.00218942]),
            ),
            (64, np.array([1.00e-03, 1.00e02]), np.array([1.87191272e-05])),
            (74, np.array([0.00e00, 1.00e36]), np.array([0.00569392])),
        ],
    )
    def test_mean_flux(self, tallies, name, ebins, expected):
        e, mf = tallies[name].mean_flux()
        np.testing.assert_array_almost_equal(e, ebins)
        np.testing.assert_array_almost_equal(mf, expected)
