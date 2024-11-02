from __future__ import annotations

from typing import Any, Final

from copy import deepcopy

# noinspection PyPackageRequirements
import pytest

from mckit.material import Composition, Element, Material


class TestElement:
    cases: Final = [
        ("H", {}),
        ("1000", {}),
        ("1001", {}),
        ("CA", {}),
        ("ca", {}),
        ("Ca", {"lib": "21C"}),
        ("CA40", {"lib": "21c"}),
        ("CA-40", {}),
        ("Ca42", {"lib": "21c"}),
        ("ca-43", {}),
        ("CA-41", {}),
        ("U", {}),
        ("U", {"isomer": 1}),
        ("U235", {}),
        ("u235", {"isomer": 1, "lib": "50c"}),
        ("U-238", {"comment": "pure 238"}),
        ("92238", {}),
        ("92000", {}),
        ("Be", {}),
        ("Be-9", {}),
        ("4000", {}),
        ("4009", {}),
        (4000, {}),
        (4009, {}),
    ]

    hash_equality: Final = [
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
    ]

    @pytest.mark.parametrize("arg1", range(len(cases)))
    @pytest.mark.parametrize("arg2", range(len(cases)))
    def test_hash(self, arg1: int, arg2: int):
        name1, options1 = self.cases[arg1]
        name2, options2 = self.cases[arg2]
        elem1 = Element(name1, **options1)
        elem2 = Element(name2, **options2)
        test_result = hash(elem1) == hash(elem2)
        assert test_result == bool(self.hash_equality[arg1][arg2])

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {
                    "charge": 1,
                    "mass_number": 0,
                    "molar_mass": 1.0079,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 1,
                    "mass_number": 0,
                    "molar_mass": 1.0079,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 1,
                    "mass_number": 1,
                    "molar_mass": 1.007825,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 0,
                    "molar_mass": 40.078,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 0,
                    "molar_mass": 40.078,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 0,
                    "molar_mass": 40.078,
                    "lib": "21c",
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 40,
                    "molar_mass": 39.962591,
                    "lib": "21c",
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 40,
                    "molar_mass": 39.962591,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 42,
                    "molar_mass": 41.958618,
                    "lib": "21c",
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 43,
                    "molar_mass": 42.958767,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 20,
                    "mass_number": 41,
                    "molar_mass": 41,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 0,
                    "molar_mass": 238.0289,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 0,
                    "molar_mass": 238.0289,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 235,
                    "molar_mass": 235.043923,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 235,
                    "molar_mass": 235.043923,
                    "lib": "50c",
                    "isomer": 1,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 238,
                    "molar_mass": 238.050783,
                    "lib": None,
                    "isomer": 0,
                    "comment": "pure 238",
                },
                {
                    "charge": 92,
                    "mass_number": 238,
                    "molar_mass": 238.050783,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 92,
                    "mass_number": 0,
                    "molar_mass": 238.0289,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 0,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 9,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 0,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 9,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 0,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
                {
                    "charge": 4,
                    "mass_number": 9,
                    "molar_mass": 9.012182,
                    "lib": None,
                    "isomer": 0,
                    "comment": None,
                },
            ]
        ),
    )
    def test_creation(self, case_no, expected):
        name, options = self.cases[case_no]
        elem = Element(name, **options)
        assert elem.charge == expected["charge"]
        assert elem.mass_number == expected["mass_number"]
        assert elem.lib == expected["lib"]
        assert elem.isomer == expected["isomer"]
        assert elem._comment == expected["comment"]
        assert elem.molar_mass == pytest.approx(expected["molar_mass"], 1.0e-4)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                [("H1", {}, 0.999885), ("H2", {}, 0.000115)],
                [("H1", {}, 0.999885), ("H2", {}, 0.000115)],
                [("H1", {}, 1.0)],
                [
                    ("CA40", {}, 0.96941),
                    ("CA42", {}, 0.00647),
                    ("CA43", {}, 0.00135),
                    ("CA44", {}, 0.02086),
                    ("CA46", {}, 0.00004),
                    ("CA48", {}, 0.00187),
                ],
                [
                    ("CA40", {}, 0.96941),
                    ("CA42", {}, 0.00647),
                    ("CA43", {}, 0.00135),
                    ("CA44", {}, 0.02086),
                    ("CA46", {}, 0.00004),
                    ("CA48", {}, 0.00187),
                ],
                [
                    ("CA40", {"lib": "21c"}, 0.96941),
                    ("CA42", {"lib": "21c"}, 0.00647),
                    ("CA43", {"lib": "21c"}, 0.00135),
                    ("CA44", {"lib": "21c"}, 0.02086),
                    ("CA46", {"lib": "21c"}, 0.00004),
                    ("CA48", {"lib": "21c"}, 0.00187),
                ],
                [("CA40", {"lib": "21c"}, 1.0)],
                [("CA40", {}, 1.0)],
                [("CA42", {"lib": "21c"}, 1.0)],
                [("CA43", {}, 1.0)],
                [],
                [
                    ("U234", {}, 0.000055),
                    ("U235", {}, 0.007200),
                    ("U238", {}, 0.992745),
                ],
                [
                    ("U234", {}, 0.000055),
                    ("U235", {}, 0.007200),
                    ("U238", {}, 0.992745),
                ],
                [("U235", {}, 1.0)],
                [("U235", {"isomer": 1, "lib": "50c"}, 1.0)],
                [("U238", {}, 1.0)],
                [("U238", {}, 1.0)],
                [
                    ("U234", {}, 0.000055),
                    ("U235", {}, 0.007200),
                    ("U238", {}, 0.992745),
                ],
                [("BE9", {}, 1.0)],
                [("BE9", {}, 1.0)],
                [("BE9", {}, 1.0)],
                [("BE9", {}, 1.0)],
                [("BE9", {}, 1.0)],
                [("BE9", {}, 1.0)],
            ]
        ),
    )
    def test_expand(self, case_no, expected):
        name, options = self.cases[case_no]
        elem = Element(name, **options)
        expanded_ans = {
            Element(name, **opt): pytest.approx(fraction, rel=1.0e-5)
            for name, opt, fraction in expected
        }
        expanded = elem.expand()
        assert expanded == expanded_ans

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                "H",
                "H",
                "H-1",
                "Ca",
                "Ca",
                "Ca",
                "Ca-40",
                "Ca-40",
                "Ca-42",
                "Ca-43",
                "Ca-41",
                "U",
                "U",
                "U-235",
                "U-235m",
                "U-238",
                "U-238",
                "U",
                "Be",
                "Be-9",
                "Be",
                "Be-9",
                "Be",
                "Be-9",
            ]
        ),
    )
    def test_str(self, case_no, expected):
        name, options = self.cases[case_no]
        elem = Element(name, **options)
        assert expected == str(elem)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                "1000",
                "1000",
                "1001",
                "20000",
                "20000",
                "20000.21c",
                "20040.21c",
                "20040",
                "20042.21c",
                "20043",
                "20041",
                "92000",
                "92000",
                "92235",
                "92235.50c",
                "92238",
                "92238",
                "92000",
                "4000",
                "4009",
                "4000",
                "4009",
                "4000",
                "4009",
            ]
        ),
    )
    def test_mcnp_repr(self, case_no, expected):
        name, options = self.cases[case_no]
        elem = Element(name, **options)
        assert expected == elem.mcnp_repr()

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                "H",
                "H",
                "H1",
                "Ca",
                "Ca",
                "Ca",
                "Ca40",
                "Ca40",
                "Ca42",
                "Ca43",
                "Ca41",
                "U",
                "U",
                "U235",
                "U235m",
                "U238",
                "U238",
                "U",
                "Be",
                "Be9",
                "Be",
                "Be9",
                "Be",
                "Be9",
            ]
        ),
    )
    def test_fispact_repr(self, case_no, expected):
        name, options = self.cases[case_no]
        elem = Element(name, **options)
        assert expected == elem.fispact_repr()

    equality: Final = [
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
    ]

    @pytest.mark.parametrize("arg1", range(len(cases)))
    @pytest.mark.parametrize("arg2", range(len(cases)))
    def test_eq(self, arg1: int, arg2: int):
        name1, options1 = self.cases[arg1]
        name2, options2 = self.cases[arg2]
        elem1 = Element(name1, **options1)
        elem2 = Element(name2, **options2)
        test_result = elem1 == elem2
        assert test_result == bool(self.equality[arg1][arg2])


class TestComposition:
    cases: Final = [
        {"atomic": [("H", 1)], "name": 1, "lib": "21c"},
        {"atomic": [("O", 5)], "name": 2, "lib": "21c"},
        {"atomic": [("H", 2), ("O", 1)], "name": 3, "lib": "21c"},
        {"weight": [("H", 1)], "name": 4, "lib": "21c"},
        {"weight": [("H", 0.11189), ("O", 0.888109)], "name": 5, "lib": "21c"},
        {"weight": [("H", 11.189), ("O", 88.8109)], "name": 6, "lib": "21c"},
        {
            "weight": [("H", 0.11189)],
            "atomic": [("O", 0.33333)],
            "name": 7,
            "lib": "21c",
        },
        {
            "atomic": [
                ("Ni-58", 68.077),
                ("Ni-60", 26.223),
                ("Ni-61", 1.140),
                ("Ni-62", 3.635),
                ("Ni-64", 0.926),
            ],
            "name": 8,
            "lib": "21c",
        },
        {
            "weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)],
            "name": 9,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479)],
            "weight": [("O", 0.23148), ("AR", 0.012886)],
            "name": 10,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479), ("O", 0.21052)],
            "weight": [("AR", 0.012886)],
            "name": 11,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479), ("Ar", 0.0046936)],
            "weight": [("O", 0.23148)],
            "name": 12,
            "lib": "21c",
        },
        {
            "atomic": [
                ("Ni-58", 68.277),
                ("Ni-60", 26.023),
                ("Ni-61", 1.140),
                ("Ni-62", 3.635),
                ("Ni-64", 0.926),
            ],
            "name": 13,
            "lib": "21c",
        },
        {
            "atomic": [
                ("Ni-58", 68.077),
                ("Ni-60", 26.223),
                ("Ni-61", 1.140),
                ("Ni-62", 3.635),
                ("Ni-64", 0.926),
                ("O", 100.0),
            ],
            "name": 14,
            "lib": "21c",
        },
        {
            "atomic": [
                ("Ni-58", 68.077),
                ("Ni-60", 26.223),
                ("Ni-61", 1.140),
                ("Ni-62", 3.635),
                ("Ni-64", 0.926),
                ("Ni", 100.0),
            ],
            "name": 15,
            "lib": "21c",
        },
    ]

    hash_eq_matrix: Final = [
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("case1", range(len(cases)))
    @pytest.mark.parametrize("case2", range(len(cases)))
    def test_hash_equal(self, compositions, case1: int, case2: int):
        comp1 = compositions[case1]
        comp2 = compositions[case2]
        assert (hash(comp1) == hash(comp2)) == bool(self.hash_eq_matrix[case1][case2])

    @pytest.fixture(scope="class")
    def compositions(self):
        return [Composition(**params) for params in self.cases]

    @pytest.mark.parametrize("case_no", range(len(cases)))
    def test_name(self, case_no: int):
        comp = Composition(**self.cases[case_no])
        assert comp.name() == case_no + 1

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {"H": 1.0},
                {"O": 1.0},
                {"H": 0.66667, "O": 0.33333},
                {"H": 1.0},
                {"H": 0.66667, "O": 0.33333},
                {"H": 0.66667, "O": 0.33333},
                {"H": 0.66667, "O": 0.33333},
                {
                    "Ni-58": 0.68077,
                    "Ni-60": 0.26223,
                    "Ni-61": 0.01140,
                    "Ni-62": 0.03635,
                    "Ni-64": 0.00926,
                },
                {"N": 0.78479, "O": 0.21052, "Ar": 0.0046936},
                {"N": 0.78479, "O": 0.21052, "Ar": 0.0046936},
                {"N": 0.78479, "O": 0.21052, "Ar": 0.0046936},
                {"N": 0.78479, "O": 0.21052, "Ar": 0.0046936},
                {
                    "Ni-58": 0.68277,
                    "Ni-60": 0.26023,
                    "Ni-61": 0.01140,
                    "Ni-62": 0.03635,
                    "Ni-64": 0.00926,
                },
                {
                    "Ni-58": 0.68077 / 2,
                    "Ni-60": 0.26223 / 2,
                    "Ni-61": 0.01140 / 2,
                    "Ni-62": 0.03635 / 2,
                    "Ni-64": 0.00926 / 2,
                    "O": 0.5,
                },
                {
                    "Ni-58": 0.68077 / 2,
                    "Ni-60": 0.26223 / 2,
                    "Ni-61": 0.01140 / 2,
                    "Ni-62": 0.03635 / 2,
                    "Ni-64": 0.00926 / 2,
                    "Ni": 0.5,
                },
            ]
        ),
    )
    def test_create(self, case_no, expected):
        comp = Composition(**self.cases[case_no])
        ans = {Element(k): pytest.approx(v, rel=1.0e-3) for k, v in expected.items()}
        assert comp._composition == ans
        inp2 = {
            "atomic": [(Element(k), v) for k, v in self.cases[case_no].get("atomic", [])],
            "weight": [(Element(k), v) for k, v in self.cases[case_no].get("weight", [])],
        }
        comp2 = Composition(**inp2)
        assert comp2._composition == ans

    @pytest.mark.parametrize(
        "_input", [{"atomic": [], "weight": []}, {"atomic": []}, {"weight": []}, {}]
    )
    def test_create_failure(self, _input):
        with pytest.raises(ValueError, match="Incorrect set of parameters."):
            Composition(**_input)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                1.0079,
                15.99903,
                6.00509,
                1.0079,
                6.00509,
                6.00509,
                6.00509,
                58.6934,
                14.551,
                14.551,
                14.551,
                14.551,
                58.6934,
                74.6928 / 2,
                58.6934,
            ]
        ),
    )
    def test_molar_mass(self, compositions, case_no, expected):
        comp = compositions[case_no]
        assert comp.molar_mass == pytest.approx(expected, rel=1.0e-3)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 1,
                    "Ni60": 1,
                    "Ni61": 1,
                    "Ni62": 1,
                    "Ni64": 1,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 1,
                    "Ar": 1,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 1,
                    "Ar": 1,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 1,
                    "Ar": 1,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 1,
                    "Ar": 1,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 1,
                    "Ni60": 1,
                    "Ni61": 1,
                    "Ni62": 1,
                    "Ni64": 1,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 1,
                    "Ni60": 1,
                    "Ni61": 1,
                    "Ni62": 1,
                    "Ni64": 1,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 1,
                    "Ni60": 1,
                    "Ni61": 1,
                    "Ni62": 1,
                    "Ni64": 1,
                    "N": 0,
                    "Ar": 0,
                },
            ]
        ),
    )
    def test_contains(self, compositions, case_no, expected):
        comp = compositions[case_no]
        for k, v in expected.items():
            assert (k in comp) == bool(v)
            assert (Element(k) in comp) == bool(v)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.66667,
                    "O": 0.33333,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.66667,
                    "O": 0.33333,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.66667,
                    "O": 0.33333,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.66667,
                    "O": 0.33333,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.68077,
                    "Ni60": 0.26223,
                    "Ni61": 0.01140,
                    "Ni62": 0.03635,
                    "Ni64": 0.00926,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0.21052,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.78479,
                    "Ar": 0.0046936,
                },
                {
                    "H": 0,
                    "O": 0.21052,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.78479,
                    "Ar": 0.0046936,
                },
                {
                    "H": 0,
                    "O": 0.21052,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.78479,
                    "Ar": 0.0046936,
                },
                {
                    "H": 0,
                    "O": 0.21052,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.78479,
                    "Ar": 0.0046936,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.68277,
                    "Ni60": 0.26023,
                    "Ni61": 0.01140,
                    "Ni62": 0.03635,
                    "Ni64": 0.00926,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0.5,
                    "Ni58": 0.68077 / 2,
                    "Ni60": 0.26223 / 2,
                    "Ni61": 0.01140 / 2,
                    "Ni62": 0.03635 / 2,
                    "Ni64": 0.00926 / 2,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.68077 / 2,
                    "Ni60": 0.26223 / 2,
                    "Ni61": 0.01140 / 2,
                    "Ni62": 0.03635 / 2,
                    "Ni64": 0.00926 / 2,
                    "N": 0,
                    "Ar": 0,
                },
            ]
        ),
    )
    def test_atomic(self, compositions, case_no, expected):
        comp = compositions[case_no]
        for k, v in expected.items():
            if v == 0:
                with pytest.raises(KeyError):
                    comp.get_atomic(k)
                with pytest.raises(KeyError):
                    comp.get_atomic(Element(k))
            else:
                assert comp.get_atomic(k) == pytest.approx(v, rel=1.0e-3)
                assert comp.get_atomic(Element(k)) == pytest.approx(v, rel=1.0e-3)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 1,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.11189,
                    "O": 0.888109,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 1,
                    "O": 0,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.11189,
                    "O": 0.888109,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.11189,
                    "O": 0.888109,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0.11189,
                    "O": 0.888109,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.6719775,
                    "Ni60": 0.267759,
                    "Ni61": 0.0118336,
                    "Ni62": 0.0383482,
                    "Ni64": 0.0100815,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0.23148,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.755465,
                    "Ar": 0.012886,
                },
                {
                    "H": 0,
                    "O": 0.23148,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.755465,
                    "Ar": 0.012886,
                },
                {
                    "H": 0,
                    "O": 0.23148,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.755465,
                    "Ar": 0.012886,
                },
                {
                    "H": 0,
                    "O": 0.23148,
                    "Ni58": 0,
                    "Ni60": 0,
                    "Ni61": 0,
                    "Ni62": 0,
                    "Ni64": 0,
                    "N": 0.755465,
                    "Ar": 0.012886,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.673952,
                    "Ni60": 0.265712,
                    "Ni61": 0.0118336,
                    "Ni62": 0.0383482,
                    "Ni64": 0.0100815,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0.21421,
                    "Ni58": 0.52804,
                    "Ni60": 0.210404,
                    "Ni61": 0.0092996,
                    "Ni62": 0.030138,
                    "Ni64": 0.0079254,
                    "N": 0,
                    "Ar": 0,
                },
                {
                    "H": 0,
                    "O": 0,
                    "Ni58": 0.6719775 / 2,
                    "Ni60": 0.267759 / 2,
                    "Ni61": 0.0118336 / 2,
                    "Ni62": 0.0383482 / 2,
                    "Ni64": 0.0100815 / 2,
                    "N": 0,
                    "Ar": 0,
                },
            ]
        ),
    )
    def test_weight(self, compositions, case_no, expected):
        comp = compositions[case_no]
        for k, v in expected.items():
            if v == 0:
                with pytest.raises(KeyError):
                    comp.get_weight(k)
                with pytest.raises(KeyError):
                    comp.get_weight(Element(k))
            else:
                assert comp.get_weight(k) == pytest.approx(v, rel=1.0e-3)
                assert comp.get_weight(Element(k)) == pytest.approx(v, rel=1.0e-3)

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {"H1": 0.999885, "H2": 0.000115},
                {"O16": 0.99757, "O17": 0.00038, "O18": 0.00205},
                {
                    "H1": 0.666593,
                    "H2": 7.666e-5,
                    "O16": 0.99757 / 3,
                    "O17": 0.00038 / 3,
                    "O18": 0.00205 / 3,
                },
                {"H1": 0.999885, "H2": 0.000115},
                {
                    "H1": 0.666593,
                    "H2": 7.666e-5,
                    "O16": 0.99757 / 3,
                    "O17": 0.00038 / 3,
                    "O18": 0.00205 / 3,
                },
                {
                    "H1": 0.666593,
                    "H2": 7.666e-5,
                    "O16": 0.99757 / 3,
                    "O17": 0.00038 / 3,
                    "O18": 0.00205 / 3,
                },
                {
                    "H1": 0.666593,
                    "H2": 7.666e-5,
                    "O16": 0.99757 / 3,
                    "O17": 0.00038 / 3,
                    "O18": 0.00205 / 3,
                },
                {
                    "Ni-58": 0.68077,
                    "Ni-60": 0.26223,
                    "Ni-61": 0.01140,
                    "Ni-62": 0.03635,
                    "Ni-64": 0.00926,
                },
                {
                    "N14": 0.99632 * 0.78479,
                    "N15": 0.00368 * 0.78479,
                    "O16": 0.99757 * 0.21052,
                    "O17": 0.00038 * 0.21052,
                    "O18": 0.00205 * 0.21052,
                    "AR36": 0.003365 * 0.0046936,
                    "Ar38": 0.000632 * 0.0046936,
                    "Ar40": 00.996003 * 0.0046936,
                },
                {
                    "N14": 0.99632 * 0.78479,
                    "N15": 0.00368 * 0.78479,
                    "O16": 0.99757 * 0.21052,
                    "O17": 0.00038 * 0.21052,
                    "O18": 0.00205 * 0.21052,
                    "AR36": 0.003365 * 0.0046936,
                    "Ar38": 0.000632 * 0.0046936,
                    "Ar40": 00.996003 * 0.0046936,
                },
                {
                    "N14": 0.99632 * 0.78479,
                    "N15": 0.00368 * 0.78479,
                    "O16": 0.99757 * 0.21052,
                    "O17": 0.00038 * 0.21052,
                    "O18": 0.00205 * 0.21052,
                    "AR36": 0.003365 * 0.0046936,
                    "Ar38": 0.000632 * 0.0046936,
                    "Ar40": 00.996003 * 0.0046936,
                },
                {
                    "N14": 0.99632 * 0.78479,
                    "N15": 0.00368 * 0.78479,
                    "O16": 0.99757 * 0.21052,
                    "O17": 0.00038 * 0.21052,
                    "O18": 0.00205 * 0.21052,
                    "AR36": 0.003365 * 0.0046936,
                    "Ar38": 0.000632 * 0.0046936,
                    "Ar40": 00.996003 * 0.0046936,
                },
                {
                    "Ni-58": 0.68277,
                    "Ni-60": 0.26023,
                    "Ni-61": 0.01140,
                    "Ni-62": 0.03635,
                    "Ni-64": 0.00926,
                },
                {
                    "Ni-58": 0.68077 / 2,
                    "Ni-60": 0.26223 / 2,
                    "Ni-61": 0.01140 / 2,
                    "Ni-62": 0.03635 / 2,
                    "Ni-64": 0.00926 / 2,
                    "O16": 0.99757 / 2,
                    "O17": 0.00038 / 2,
                    "O18": 0.00205 / 2,
                },
                {
                    "Ni-58": 0.68077,
                    "Ni-60": 0.26223,
                    "Ni-61": 0.01140,
                    "Ni-62": 0.03635,
                    "Ni-64": 0.00926,
                },
            ]
        ),
    )
    def test_expand(self, compositions, case_no, expected):
        comp = compositions[case_no]
        expanded = comp.expand()
        ans = {Element(k): pytest.approx(v, rel=1.0e-3) for k, v in expected.items()}
        assert ans == expanded._composition

    @pytest.mark.parametrize(
        "case_no, expected",
        enumerate(
            [
                {"atomic": [("H", 1)]},
                {"atomic": [("O", 1)]},
                {"atomic": [("H", 2), ("O", 1)]},
                {"atomic": [("H", 1)]},
                {"atomic": [("H", 2), ("O", 1)]},
                {"atomic": [("H", 2), ("O", 1)]},
                {"atomic": [("H", 2), ("O", 1)]},
                {"atomic": [("Ni", 1.0)]},
                {"weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)]},
                {"weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)]},
                {"weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)]},
                {"weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)]},
                None,
                {"atomic": [("Ni", 0.5), ("O", 0.5)]},
                {"atomic": [("Ni", 1.0)]},
            ]
        ),
    )
    def test_natural(self, compositions, case_no, expected):
        comp = compositions[case_no]
        nat = comp.natural(tolerance=1.0e-3)
        if expected is None:
            assert nat is None
        else:
            ans = {k: pytest.approx(v, rel=1.0e-3) for k, v in Composition(**expected)}
            assert nat._composition == ans

    eq_matrix: Final = [
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("case1", range(len(cases)))
    @pytest.mark.parametrize("case2", range(len(cases)))
    def test_equal(self, compositions, case1: int, case2: int):
        comp1 = compositions[case1]
        comp2 = compositions[case2]
        assert (comp1 == comp2) == bool(self.eq_matrix[case1][case2])

    @pytest.mark.parametrize(
        "case_no, name, expected_kw",
        [
            (0, 1, {"lib": "21c"}),
            (1, 2, {"lib": "21c"}),
            (2, 3, {"lib": "21c"}),
            (3, 4, {"lib": "21c"}),
            (4, 5, {"lib": "21c"}),
            (5, 6, {"lib": "21c"}),
            (6, 7, {"lib": "21c"}),
            (7, 8, {"lib": "21c"}),
            (8, 9, {"lib": "21c"}),
            (9, 10, {"lib": "21c"}),
            (10, 11, {"lib": "21c"}),
            (11, 12, {"lib": "21c"}),
            (12, 13, {"lib": "21c"}),
        ],
    )
    def test_get_option(self, compositions, case_no, name, expected_kw):
        comp = compositions[case_no]
        assert comp.name() == name
        for key, value in expected_kw.items():
            assert comp[key] == value

    @pytest.mark.parametrize(
        "mix_components, ans_index",
        [
            ([(0, 1)], 0),
            ([(0, 2)], 0),
            ([(0, 2), (1, 1)], 2),
            ([(7, 1), (1, 1)], 13),
            ([(0, 1), (1, 1), (0, 1)], 2),
            ([(7, 1), (1, 0.5), (1, 0.5)], 13),
        ],
    )
    def test_mixture(self, compositions, mix_components, ans_index):
        to_mix = [(compositions[i], f) for i, f in mix_components]
        mixture = Composition.mixture(*to_mix)
        assert mixture == compositions[ans_index]


class TestMaterial:
    cases: Final[list[dict[str, Any]]] = [
        {
            "weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)],
            "density": 1.2929e-3,
            "name": 1,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479)],
            "weight": [("O", 0.23148), ("AR", 0.012886)],
            "density": 1.2929e-3,
            "name": 1,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479), ("O", 0.21052)],
            "weight": [("AR", 0.012886)],
            "concentration": 5.3509e19,
            "name": 1,
            "lib": "21c",
        },
        {
            "atomic": [("N", 0.78479), ("Ar", 0.0046936)],
            "weight": [("O", 0.23148)],
            "concentration": 5.3509e19,
            "name": 1,
            "lib": "21c",
        },
        {"atomic": [("N", 1)], "density": 1.251e-3},
        {"atomic": [("O", 1)], "density": 1.42897e-3},
        {"atomic": [("Ar", 1)], "density": 1.784e-3},
    ]

    materials: Final[list[Material]] = [Material(**c) for c in cases]

    @pytest.mark.parametrize(
        "data, msg",
        [
            ({}, "Neither 'composition', nor 'atomic' or 'weight' parameters are specified."),
            ({"atomic": [("N", 1)]}, "Neither concentration nor density is specified"),
            ({"weight": [("N", 1)]}, "Neither concentration nor density is specified"),
            (
                {"atomic": [("N", 1)], "weight": [("N", 1)]},
                "Neither concentration nor density is specified",
            ),
            (
                {"composition": {"atomic": [("N", 1)]}},
                "Neither concentration nor density is specified",
            ),
            (
                {"composition": {"atomic": [("N", 1)]}, "atomic": [("N", 1)]},
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {"composition": {"atomic": [("N", 1)]}, "weight": [("N", 1)]},
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "composition": {"atomic": [("N", 1)]},
                    "atomic": [("N", 1)],
                    "weight": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {"density": 7.8},
                "Neither 'composition', nor 'atomic' or 'weight' parameters are specified.",
            ),
            (
                {"concentration": 1.0e23},
                "Neither 'composition', nor 'atomic' or 'weight' parameters are specified.",
            ),
            (
                {"density": 7.8, "concentration": 1.0e23},
                "Neither 'composition', nor 'atomic' or 'weight' parameters are specified.",
            ),
            (
                {"density": 7.8, "concentration": 1.0e23, "atomic": [("N", 1)]},
                "Both concentration and density are specified",
            ),
            (
                {"density": 7.8, "concentration": 1.0e23, "weight": [("N", 1)]},
                "Both concentration and density are specified",
            ),
            (
                {
                    "density": 7.8,
                    "concentration": 1.0e23,
                    "atomic": [("N", 1)],
                    "weight": [("N", 1)],
                },
                "Both concentration and density are specified",
            ),
            (
                {
                    "density": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "atomic": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "density": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "weight": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "density": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "atomic": [("N", 1)],
                    "weight": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "concentration": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "atomic": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "concentration": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "weight": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
            (
                {
                    "concentration": 7.8,
                    "composition": {"atomic": [("N", 1)]},
                    "atomic": [("N", 1)],
                    "weight": [("N", 1)],
                },
                "composition is specified along with 'atomic' or 'weight' parameters",
            ),
        ],
    )
    def test_creation_failure(self, data: dict[str, Any], msg):
        data = deepcopy(data)  # this fixes pytest strange behavior (see below)"
        if "composition" in data.keys():
            composition_params = data.pop("composition")
            assert not isinstance(
                composition_params, Composition
            ), "Check some strange behavior on 'pytest test/*.py': arriving params are already Composition"
            composition = Composition(**composition_params)
        else:
            composition = None
        with pytest.raises(ValueError, match=msg):
            Material(**data, composition=composition)

    @pytest.mark.parametrize("case", cases)
    def test_creation(self, case):
        mat1 = Material(**case)
        data = case.copy()
        atomic = data.pop("atomic", ())
        weight = data.pop("weight", ())
        comp = Composition(atomic=atomic, weight=weight)
        mat2 = Material(composition=comp, **data)
        assert mat1.composition == comp
        assert mat2.composition == comp
        if "density" in data.keys():
            d = pytest.approx(data["density"], rel=1.0e-5)
            assert mat1.density == d
            assert mat2.density == d
        elif "concentration" in data.keys():
            d = pytest.approx(data["concentration"], rel=1.0e-5)
            assert mat1.concentration == d
            assert mat2.concentration == d

    hash_eq_matrix: Final = [
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("case1", range(len(cases)))
    @pytest.mark.parametrize("case2", range(len(cases)))
    def test_hash_equal(self, case1: int, case2: int):
        mat1 = TestMaterial.materials[case1]
        mat2 = TestMaterial.materials[case2]
        assert (hash(mat1) == hash(mat2)) == bool(self.hash_eq_matrix[case1][case2])

    eq_matrix: Final = [
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1],
    ]

    @pytest.mark.parametrize("case1", range(len(cases)))
    @pytest.mark.parametrize("case2", range(len(cases)))
    def test_equal(self, case1: int, case2: int):
        mat1 = TestMaterial.materials[case1]
        mat2 = TestMaterial.materials[case2]
        assert (mat1 == mat2) == bool(self.eq_matrix[case1][case2])

    @pytest.mark.parametrize("case_no", range(len(cases)))
    @pytest.mark.parametrize(
        "data",
        [{"new_vol": 5, "old_vol": 2.5}, {"new_vol": 4, "old_vol": 6}, {"factor": 2}],
    )
    def test_correct(self, case_no: int, data):
        mat = TestMaterial.materials[case_no]
        new_mat = mat.correct(**data)
        assert mat.composition == new_mat.composition
        if "factor" in data.keys():
            ans_den = pytest.approx(mat.density * data["factor"], rel=1.0e-10)
            assert new_mat.density == ans_den
        else:
            old_mass = data["old_vol"] * mat.density
            new_mass = data["new_vol"] * new_mat.density
            assert old_mass == pytest.approx(new_mass, rel=1.0e-10)

    @pytest.mark.parametrize(
        "input_data, expected",
        [
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1)], "volume"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 0.8)], "volume"),
                {"atomic": [("N", 1)], "density": 1.251e-3 * 0.8},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1.2)], "volume"),
                {"atomic": [("N", 1)], "density": 1.251e-3 * 1.2},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1)], "weight"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 0.8)], "weight"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1.2)], "weight"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1)], "atomic"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 0.8)], "atomic"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                ([({"atomic": [("N", 1)], "density": 1.251e-3}, 1.2)], "atomic"),
                {"atomic": [("N", 1)], "density": 1.251e-3},
            ),
            (
                (
                    [
                        ({"atomic": [("N", 1)], "density": 1.251e-3}, 0.78084),
                        ({"atomic": [("O", 1)], "density": 1.42897e-3}, 0.20948),
                        ({"atomic": [("Ar", 1)], "density": 1.784e-3}, 0.00934),
                    ],
                    "volume",
                ),
                {
                    "weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)],
                    "density": 1.2929e-3,
                },
            ),
            (
                (
                    [
                        ({"atomic": [("N", 1)], "density": 1.251e-3}, 0.755465),
                        ({"atomic": [("O", 1)], "density": 1.42897e-3}, 0.23148),
                        ({"atomic": [("Ar", 1)], "density": 1.784e-3}, 0.012886),
                    ],
                    "weight",
                ),
                {
                    "weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)],
                    "density": 1.2929e-3,
                },
            ),
            (
                (
                    [
                        ({"atomic": [("N", 1)], "density": 1.251e-3}, 0.78479),
                        ({"atomic": [("O", 1)], "density": 1.42897e-3}, 0.21052),
                        ({"atomic": [("Ar", 1)], "density": 1.784e-3}, 0.0046936),
                    ],
                    "atomic",
                ),
                {
                    "weight": [("N", 0.755465), ("O", 0.23148), ("AR", 0.012886)],
                    "density": 1.2929e-3,
                },
            ),
        ],
    )
    def test_mixture(self, input_data, expected):
        materials, fraction_type = input_data
        materials = [(Material(**kws), fraction) for kws, fraction in materials]
        ans_mat = Material(**expected)
        mix = Material.mixture(*materials, fraction_type=fraction_type)
        assert ans_mat == mix
