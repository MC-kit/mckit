from __future__ import annotations

from typing import Final

import pytest

from mckit.source import Distribution, Source, create_bin_distributions


class TestDistribution:
    @pytest.mark.parametrize(
        "name, values, probs",
        [
            (1, [1, 2, 3], [1, 2, 3, 4, 5]),
            (2, [1, 2, 3], [1, 2, 3, 4]),
            (3, [1, 2, 3, 4], [1, 2]),
            (4, [1, 2, 3, 4], Distribution(1, [1, 2], [1, 2])),
        ],
    )
    def test_create_failure(self, name, values, probs):
        with pytest.raises(ValueError, match="Inconsistent size of values."):
            Distribution(name, values, probs)

    @pytest.mark.parametrize(
        "name, values, probs, var",
        [
            (1, [1, 2, 3], [1, 2, 3], "X"),
            (2, [1, 2, 3, 4], [1, 2, 3], "Y"),
            (3, [[0.1, 0.5, 0.4], [1, 0, 0]], [0.3, 0.7], "VEC"),
        ],
    )
    def test_create(self, name, values, probs, var):
        d = Distribution(name, values, probs, distribution_variable=var)
        assert d.name == name
        assert d.size == len(probs)
        assert len(d) == len(probs)
        assert d.variable == var

    @pytest.mark.parametrize(
        "name, values, probs, expected_names",
        [
            (1, [1, 2, 3], [1, 2, 3], set()),
            (
                2,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                [1, 2],
                {10, 11},
            ),
            (
                3,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                Distribution(12, [1, 2], [1, 2]),
                {10, 11},
            ),
            (1, [1, 2, 3], Distribution(12, [1, 2], [1, 2]), set()),
        ],
    )
    def test_get_inner(self, name, values, probs, expected_names):
        d = Distribution(name, values, probs)
        inner = d.get_inner()
        inner_names = {i.name for i in inner}
        assert inner_names == expected_names

    @pytest.mark.parametrize(
        "name, values, probs, discrete, expected",
        [
            (1, [1, 2, 3], [4, 5, 6], True, "SI1 L 1 2 3\nSP1 D 4 5 6"),
            (2, [1, 2, 3], [4, 5], False, "SI2 H 1 2 3\nSP2 D 0 4 5"),
            (3, [1, 2, 3], Distribution(4, [4, 5, 6], [7, 8, 9]), True, "DS3 L 1 2 3"),
            (
                4,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                [1, 2],
                False,
                "SI4 S 10 11\nSP4 D 1 2",
            ),
            (
                5,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                Distribution(12, [1, 2], [1, 2]),
                False,
                "DS5 S 10 11",
            ),
            (
                4,
                [[0.5, 0.3, -0.2], [-0.9, 0, 0.4]],
                [0.3, 0.7],
                True,
                "SI4 L 0.5 0.3 -0.2 -0.9 0.0 0.4\nSP4 D 0.3 0.7",
            ),
            (
                5,
                [[0, -1, 0], [0.5, 0, 0.3]],
                Distribution(4, [5, 6], [7, 8]),
                True,
                "DS5 L 0.0 -1.0 0.0 0.5 0.0 0.3",
            ),
            (6, [1, 2, 3], [4, 5, 6], False, "SI6 A 1 2 3\nSP6 4 5 6"),
        ],
    )
    def test_mcnp_repr(self, name, values, probs, discrete, expected):
        d = Distribution(name, values, probs, is_discrete=discrete)
        assert d.mcnp_repr() == expected

    @pytest.mark.parametrize(
        "name, values, probs, expected",
        [
            (1, [1, 2, 3], [4, 5, 6], None),
            (2, [1, 2, 3], [4, 5], None),
            (3, [1, 2, 3], Distribution(4, [4, 5, 6], [7, 8, 9]), 0),
            (
                4,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                [1, 2],
                None,
            ),
            (
                5,
                [Distribution(10, [1, 2], [1, 2]), Distribution(11, [1, 2], [2])],
                Distribution(12, [1, 2], [1, 2]),
                0,
            ),
        ],
    )
    def test_depends_on(self, name, values, probs, expected):
        d = Distribution(name, values, probs)
        if expected is None:
            assert d.depends_on() is None
        else:
            assert d.depends_on() is probs

    def test_invalid_values(self):
        values = [Distribution(1, [1, 2], [1]), [1, 2, 3]]
        probs = [0.5, 0.5]
        with pytest.raises(TypeError):
            Distribution("RAD", values, probs)
        with pytest.raises(TypeError):
            Distribution("RAD", values[::-1], probs)


@pytest.mark.parametrize(
    "free_number, bins, expected",
    [
        (1, [1, 2], [Distribution(1, [1, 2], [1])]),
        (10, [1, 2, 3], [Distribution(10, [1, 2], [1]), Distribution(11, [2, 3], [1])]),
    ],
)
def test_create_bin_distributions(free_number, bins, expected):
    new_free_number, actual = create_bin_distributions(bins, free_number)
    assert new_free_number == free_number + len(actual)
    for a, e in zip(actual, expected, strict=False):
        assert a.mcnp_repr() == e.mcnp_repr()


class TestSource:
    distrs: Final = [
        Distribution(1, [1, 2], [1]),
        Distribution(2, [2, 3], [1]),
        Distribution(3, [4, 5, 6], [1, 2, 3], "X", True),
    ]

    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            ({"PAR": 1, "ERG": 14}, "SDEF PAR=1 ERG=14"),
            ({"PAR": 1, "X": distrs[0]}, "SDEF PAR=1 X=D1\nSI1 H 1 2\nSP1 D 0 1"),
            (
                {"PAR": 2, "X": distrs[0], "Y": distrs[2]},
                "SDEF PAR=2 X=D1 Y=D3\nSI1 H 1 2\nSP1 D 0 1\nSI3 L 4 5 6\nSP3 D 1 2 3",
            ),
            (
                {
                    "PAR": 2,
                    "X": distrs[2],
                    "Y": Distribution(2, [1, 2, 3], distrs[2], is_discrete=True),
                },
                "SDEF PAR=2 X=D3 Y=FX D2\nSI3 L 4 5 6\nSP3 D 1 2 3\nDS2 L 1 2 3",
            ),
            (
                {
                    "PAR": 3,
                    "X": distrs[2],
                    "Y": Distribution(
                        4,
                        create_bin_distributions([2, 3, 4, 5], 10)[1],
                        distrs[2],
                    ),
                    "Z": Distribution(
                        5,
                        create_bin_distributions([6, 7, 8, 9], 13)[1],
                        distrs[2],
                    ),
                },
                "SDEF PAR=3 X=D3 Y=FX D4 Z=FX D5\nSI3 L 4 5 6\nSP3 D 1 2 3\n"
                "DS4 S 10 11 12\nDS5 S 13 14 15\nSI10 H 2 3\nSP10 D 0 1\n"
                "SI11 H 3 4\nSP11 D 0 1\nSI12 H 4 5\nSP12 D 0 1\n"
                "SI13 H 6 7\nSP13 D 0 1\nSI14 H 7 8\nSP14 D 0 1\n"
                "SI15 H 8 9\nSP15 D 0 1",
            ),
        ],
    )
    def test_mcnp_repr(self, kwargs, expected):
        src = Source(**kwargs)
        assert src.mcnp_repr() == expected
