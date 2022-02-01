import numpy as np
import pytest

from mckit.parser.mctal_parser import read_mctal
from mckit.utils import filename_resolver

file_resolver = filename_resolver("tests")


@pytest.mark.parametrize(
    "mctal_file, expected",
    [
        (
            "parser_test_data/mctal.t",
            {
                4: {
                    "name": 4,
                    "particles": {"N"},
                    "type": "Non",
                    "dims": [4],
                    "vars": ["f"],
                    "bins": [[1, 2, 3, 4]],
                    "comment": "One line comment",
                    "data": np.array(
                        [8.80794e-05, 1.50383e-05, 2.11945e-06, 8.56005e-06]
                    ),
                    "error": np.array([0.0004, 0.0044, 0.0094, 0.0015]),
                },
                5: {
                    "name": 5,
                    "particles": {"N"},
                    "type": "Point",
                    "comment": "This is"
                    + " " * 70
                    + "\n     multiline"
                    + " " * 68
                    + "\n     comment",
                    "dims": [2, 17],
                    "vars": ["d", "e"],
                    "bins": [
                        [0, 1],
                        [
                            0.00000e00,
                            9.33333e-01,
                            1.86667e00,
                            2.80000e00,
                            3.73333e00,
                            4.66667e00,
                            5.60000e00,
                            6.53333e00,
                            7.46667e00,
                            8.40000e00,
                            9.33333e00,
                            1.02667e01,
                            1.12000e01,
                            1.21333e01,
                            1.30667e01,
                            1.40000e01,
                        ],
                    ],
                    "data": np.array(
                        [
                            [
                                0.00000e00,
                                1.58216e-06,
                                1.87159e-07,
                                6.61835e-08,
                                2.77078e-08,
                                1.91715e-08,
                                2.10682e-08,
                                1.63592e-08,
                                2.00616e-08,
                                7.62970e-09,
                                1.07499e-08,
                                1.65694e-08,
                                2.26494e-08,
                                2.65932e-08,
                                1.63491e-08,
                                9.16554e-09,
                                2.04958e-06,
                            ],
                            [
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                0.00000e00,
                                6.20784e-10,
                                6.90270e-10,
                                1.42735e-09,
                                1.00714e-09,
                                7.39058e-10,
                                4.48460e-09,
                            ],
                        ]
                    ),
                    "error": np.array(
                        [
                            [
                                0.0000,
                                0.0093,
                                0.0105,
                                0.0162,
                                0.0267,
                                0.0360,
                                0.0353,
                                0.0322,
                                0.0298,
                                0.0493,
                                0.0459,
                                0.0336,
                                0.0321,
                                0.0300,
                                0.0414,
                                0.0601,
                                0.0076,
                            ],
                            [
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0000,
                                0.0005,
                                0.0004,
                                0.0002,
                                0.0004,
                                0.0005,
                                0.0001,
                            ],
                        ]
                    ),
                },
                14: {
                    "name": 14,
                    "particles": {"N"},
                    "type": "Non",
                    "comment": "",
                    "dims": [3, 2, 17],
                    "vars": ["f", "m", "e"],
                    "bins": [
                        [1, 2, 3],
                        [0, 1],
                        [
                            0.00000e00,
                            9.33333e-01,
                            1.86667e00,
                            2.80000e00,
                            3.73333e00,
                            4.66667e00,
                            5.60000e00,
                            6.53333e00,
                            7.46667e00,
                            8.40000e00,
                            9.33333e00,
                            1.02667e01,
                            1.12000e01,
                            1.21333e01,
                            1.30667e01,
                            1.40000e01,
                        ],
                    ],
                    "data": np.array(
                        [
                            [
                                [
                                    0.00000e00,
                                    9.64735e-09,
                                    6.09468e-07,
                                    1.32468e-06,
                                    1.09940e-06,
                                    1.00315e-06,
                                    9.19119e-07,
                                    8.83431e-07,
                                    1.09927e-06,
                                    1.16016e-06,
                                    1.43665e-06,
                                    3.69534e-06,
                                    6.30478e-06,
                                    1.00136e-05,
                                    5.43929e-06,
                                    3.03981e-06,
                                    3.80378e-05,
                                ],
                                [
                                    0.00000e00,
                                    2.48959e-04,
                                    2.39806e-07,
                                    8.52906e-08,
                                    2.85414e-08,
                                    9.16832e-09,
                                    3.49531e-09,
                                    1.89229e-09,
                                    1.36790e-09,
                                    1.19742e-09,
                                    1.49466e-09,
                                    4.43477e-09,
                                    7.74861e-09,
                                    1.18686e-08,
                                    5.52138e-09,
                                    2.36672e-09,
                                    2.49363e-04,
                                ],
                            ],
                            [
                                [
                                    0.00000e00,
                                    6.56033e-09,
                                    2.51919e-07,
                                    3.07402e-07,
                                    1.25075e-07,
                                    1.00504e-07,
                                    9.04613e-08,
                                    8.45778e-08,
                                    1.20215e-07,
                                    7.73971e-08,
                                    8.84206e-08,
                                    1.33830e-07,
                                    1.80750e-07,
                                    2.16944e-07,
                                    1.29120e-07,
                                    6.92425e-08,
                                    1.98242e-06,
                                ],
                                [
                                    0.00000e00,
                                    8.63466e-05,
                                    1.26651e-07,
                                    2.12696e-08,
                                    3.34729e-09,
                                    9.23087e-10,
                                    3.42818e-10,
                                    1.84524e-10,
                                    1.49631e-10,
                                    7.98288e-11,
                                    9.18360e-11,
                                    1.58698e-10,
                                    2.22582e-10,
                                    2.58535e-10,
                                    1.35119e-10,
                                    5.63011e-11,
                                    8.65005e-05,
                                ],
                            ],
                            [
                                [
                                    0.00000e00,
                                    1.13397e-09,
                                    3.11299e-08,
                                    3.65827e-08,
                                    1.37816e-08,
                                    1.03438e-08,
                                    1.13258e-08,
                                    1.12447e-08,
                                    1.83109e-08,
                                    8.58871e-09,
                                    8.87751e-09,
                                    1.71934e-08,
                                    2.18344e-08,
                                    2.53578e-08,
                                    1.51028e-08,
                                    7.96793e-09,
                                    2.38776e-07,
                                ],
                                [
                                    0.00000e00,
                                    1.94119e-05,
                                    1.76797e-08,
                                    2.54610e-09,
                                    3.68989e-10,
                                    9.48239e-11,
                                    4.25000e-11,
                                    2.46131e-11,
                                    2.29424e-11,
                                    8.80678e-12,
                                    9.18887e-12,
                                    2.03863e-11,
                                    2.69006e-11,
                                    3.02948e-11,
                                    1.58845e-11,
                                    6.57886e-12,
                                    1.94328e-05,
                                ],
                            ],
                        ]
                    ),
                    "error": np.array(
                        [
                            [
                                [
                                    0.0000,
                                    0.0018,
                                    0.0012,
                                    0.0011,
                                    0.0012,
                                    0.0013,
                                    0.0014,
                                    0.0016,
                                    0.0017,
                                    0.0017,
                                    0.0016,
                                    0.0011,
                                    0.0008,
                                    0.0006,
                                    0.0009,
                                    0.0013,
                                    0.0004,
                                ],
                                [
                                    0.0000,
                                    0.0021,
                                    0.0009,
                                    0.0011,
                                    0.0012,
                                    0.0013,
                                    0.0014,
                                    0.0016,
                                    0.0017,
                                    0.0017,
                                    0.0016,
                                    0.0011,
                                    0.0008,
                                    0.0006,
                                    0.0009,
                                    0.0013,
                                    0.0021,
                                ],
                            ],
                            [
                                [
                                    0.0000,
                                    0.0123,
                                    0.0080,
                                    0.0090,
                                    0.0124,
                                    0.0148,
                                    0.0167,
                                    0.0186,
                                    0.0198,
                                    0.0223,
                                    0.0220,
                                    0.0185,
                                    0.0163,
                                    0.0150,
                                    0.0201,
                                    0.0295,
                                    0.0054,
                                ],
                                [
                                    0.0000,
                                    0.0241,
                                    0.0063,
                                    0.0092,
                                    0.0128,
                                    0.0151,
                                    0.0168,
                                    0.0185,
                                    0.0198,
                                    0.0222,
                                    0.0220,
                                    0.0186,
                                    0.0163,
                                    0.0150,
                                    0.0201,
                                    0.0294,
                                    0.0241,
                                ],
                            ],
                            [
                                [
                                    0.0000,
                                    0.0823,
                                    0.0313,
                                    0.0353,
                                    0.0552,
                                    0.0638,
                                    0.0593,
                                    0.0654,
                                    0.0606,
                                    0.0918,
                                    0.0861,
                                    0.0633,
                                    0.0580,
                                    0.0539,
                                    0.0706,
                                    0.1043,
                                    0.0163,
                                ],
                                [
                                    0.0000,
                                    0.1095,
                                    0.0227,
                                    0.0362,
                                    0.0573,
                                    0.0677,
                                    0.0604,
                                    0.0653,
                                    0.0606,
                                    0.0917,
                                    0.0860,
                                    0.0634,
                                    0.0580,
                                    0.0539,
                                    0.0703,
                                    0.1037,
                                    0.1094,
                                ],
                            ],
                        ]
                    ),
                },
                24: {
                    "name": 24,
                    "particles": {"N"},
                    "type": "Non",
                    "comment": "",
                    "dims": [2, 6, 7],
                    "vars": ["f", "u", "e"],
                    "bins": [
                        [2, 3],
                        [0, 1, 2, 3, 4, 5],
                        [
                            0.0000e00,
                            3.0000e00,
                            6.0000e00,
                            9.0000e00,
                            1.2000e01,
                            1.5000e01,
                        ],
                    ],
                    "data": np.array(
                        [
                            [
                                [
                                    0.00000e00,
                                    5.72625e-08,
                                    3.36136e-08,
                                    2.99109e-08,
                                    5.03426e-08,
                                    0.00000e00,
                                    1.71130e-07,
                                ],
                                [
                                    0.00000e00,
                                    1.12613e-07,
                                    6.67524e-08,
                                    5.45806e-08,
                                    1.26970e-07,
                                    0.00000e00,
                                    3.60916e-07,
                                ],
                                [
                                    0.00000e00,
                                    2.29959e-07,
                                    1.25578e-07,
                                    1.25896e-07,
                                    2.90195e-07,
                                    0.00000e00,
                                    7.71627e-07,
                                ],
                                [
                                    0.00000e00,
                                    1.28752e-07,
                                    6.58607e-08,
                                    6.13112e-08,
                                    6.26042e-08,
                                    1.20676e-07,
                                    4.39204e-07,
                                ],
                                [
                                    0.00000e00,
                                    6.79069e-08,
                                    3.00027e-08,
                                    3.27493e-08,
                                    2.63134e-08,
                                    8.25692e-08,
                                    2.39542e-07,
                                ],
                                [
                                    0.00000e00,
                                    5.96493e-07,
                                    3.21807e-07,
                                    3.04448e-07,
                                    5.56425e-07,
                                    2.03245e-07,
                                    1.98242e-06,
                                ],
                            ],
                            [
                                [
                                    0.00000e00,
                                    7.21429e-09,
                                    4.22791e-09,
                                    3.44185e-09,
                                    6.45356e-09,
                                    0.00000e00,
                                    2.13376e-08,
                                ],
                                [
                                    0.00000e00,
                                    1.42111e-08,
                                    7.67042e-09,
                                    6.38826e-09,
                                    1.57524e-08,
                                    0.00000e00,
                                    4.40222e-08,
                                ],
                                [
                                    0.00000e00,
                                    2.76409e-08,
                                    1.38688e-08,
                                    1.62544e-08,
                                    3.35833e-08,
                                    0.00000e00,
                                    9.13475e-08,
                                ],
                                [
                                    0.00000e00,
                                    1.59835e-08,
                                    7.21256e-09,
                                    9.03184e-09,
                                    7.71240e-09,
                                    1.37593e-08,
                                    5.36996e-08,
                                ],
                                [
                                    0.00000e00,
                                    7.66382e-09,
                                    3.31290e-09,
                                    4.85495e-09,
                                    2.55185e-09,
                                    9.98544e-09,
                                    2.83690e-08,
                                ],
                                [
                                    0.00000e00,
                                    7.27137e-08,
                                    3.62926e-08,
                                    3.99713e-08,
                                    6.60534e-08,
                                    2.37447e-08,
                                    2.38776e-07,
                                ],
                            ],
                        ]
                    ),
                    "error": np.array(
                        [
                            [
                                [
                                    0.0000,
                                    0.0231,
                                    0.0309,
                                    0.0410,
                                    0.0329,
                                    0.0000,
                                    0.0183,
                                ],
                                [
                                    0.0000,
                                    0.0162,
                                    0.0219,
                                    0.0297,
                                    0.0210,
                                    0.0000,
                                    0.0128,
                                ],
                                [
                                    0.0000,
                                    0.0110,
                                    0.0155,
                                    0.0195,
                                    0.0136,
                                    0.0000,
                                    0.0086,
                                ],
                                [
                                    0.0000,
                                    0.0150,
                                    0.0214,
                                    0.0275,
                                    0.0272,
                                    0.0211,
                                    0.0116,
                                ],
                                [
                                    0.0000,
                                    0.0201,
                                    0.0313,
                                    0.0379,
                                    0.0404,
                                    0.0269,
                                    0.0161,
                                ],
                                [
                                    0.0000,
                                    0.0069,
                                    0.0098,
                                    0.0125,
                                    0.0098,
                                    0.0166,
                                    0.0054,
                                ],
                            ],
                            [
                                [
                                    0.0000,
                                    0.0786,
                                    0.1042,
                                    0.1448,
                                    0.1081,
                                    0.0000,
                                    0.0548,
                                ],
                                [
                                    0.0000,
                                    0.0526,
                                    0.0743,
                                    0.1044,
                                    0.0701,
                                    0.0000,
                                    0.0381,
                                ],
                                [
                                    0.0000,
                                    0.0390,
                                    0.0560,
                                    0.0622,
                                    0.0462,
                                    0.0000,
                                    0.0260,
                                ],
                                [
                                    0.0000,
                                    0.0506,
                                    0.0768,
                                    0.0858,
                                    0.0920,
                                    0.0746,
                                    0.0344,
                                ],
                                [
                                    0.0000,
                                    0.0709,
                                    0.1118,
                                    0.1183,
                                    0.1642,
                                    0.0910,
                                    0.0486,
                                ],
                                [
                                    0.0000,
                                    0.0238,
                                    0.0345,
                                    0.0407,
                                    0.0331,
                                    0.0577,
                                    0.0163,
                                ],
                            ],
                        ]
                    ),
                },
            },
        )
    ],
)
def test_mctal_parser(mctal_file, expected):
    mctal_file = file_resolver(mctal_file)
    tallies = read_mctal(mctal_file)
    assert tallies.keys() == expected.keys()
    for name, tally in tallies.items():
        assert tally.keys() == expected[name].keys()
        assert tally["name"] == expected[name]["name"]
        assert tally["particles"] == expected[name]["particles"]
        assert tally["type"] == expected[name]["type"]
        assert tally["dims"] == expected[name]["dims"]
        assert tally["vars"] == expected[name]["vars"]
        assert tally["bins"] == expected[name]["bins"]
        np.testing.assert_array_almost_equal(
            tally["data"], expected[name]["data"], decimal=2
        )
        np.testing.assert_array_almost_equal(tally["error"], expected[name]["error"])