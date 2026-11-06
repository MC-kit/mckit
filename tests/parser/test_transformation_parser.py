from __future__ import annotations

import pytest

import mckit.parser.common.utils as cmn
import mckit.parser.transformation_parser as trp

from mckit.transformation import Transformation


# noinspection PyTypeChecker
@pytest.mark.parametrize(
    "text,expected",
    [
        ("tr2 0 0 1", Transformation(translation=[0.0, 0.0, 1.0], name=2)),
        (
            " *tr2 0 0 1 45 45 90 135 45 90 90 90 0",
            Transformation(
                translation=[0.0, 0.0, 1.0],
                rotation=[45, 45, 90, 135, 45, 90, 90, 90, 0],
                indegrees=True,
                name=2,
            ),
        ),
        (
            "*tr1 0. 0. 0. 3.62 86.38 90. 93.62 3.62 90. 90. 90. 0.",
            Transformation(
                translation=[0.0, 0.0, 0.0],
                rotation=[3.62, 86.38, 90.0, 93.62, 3.62, 90.0, 90.0, 90.0, 0.0],
                indegrees=True,
                name=1,
            ),
        ),
    ],
)
def test_transformation_parser(text, expected):
    actual = trp.parse(text)
    assert actual == expected


@pytest.mark.parametrize(
    "text,msg",
    [
        ("2 0 0 1", "Transformation specification must start with 'tr<number>'"),
        ("tr2", "Transformation specification requires a translation vector of 3 numbers"),
        ("tr2 1 2 3 4", "Invalid number of transformation rotation parameters: 1"),
        ("tr2 1 2 3 1 2 3 4 5 6 7 8 9 1.5", "The M option should be specified as an integer"),
    ],
)
def test_bad_transformation_spec(text, msg):
    with pytest.raises(cmn.ParseError, match=msg):
        trp.parse(text)


def test_wrong_m_option_value():
    with pytest.raises(ValueError, match="Invalid M option value 10"):
        trp.parse("tr2 1 2 3 1 2 3 4 5 6 7 8 9 10")


if __name__ == "__main__":
    pytest.main()
