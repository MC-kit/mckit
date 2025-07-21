from __future__ import annotations

import pytest

import mckit.parser.transformation_parser as trp

from mckit.transformation import Transformation


@pytest.mark.parametrize(
    "text,expected_types,expected_values",
    [
        (
            "tr1 0 0 1.0",
            ["NAME", "INTEGER", "INTEGER", "FLOAT"],
            [(1, False), 0, 0, 1.0],
        ),
        (
            "*tr1 0 0 1.0",
            ["NAME", "INTEGER", "INTEGER", "FLOAT"],
            [(1, True), 0, 0, 1.0],
        ),
    ],
)
def test_transformation_lexer(text, expected_types, expected_values):
    lexer = trp.Lexer()
    tokens = list(lexer.tokenize(text))
    actual_types = [t.type for t in tokens]
    assert actual_types == expected_types
    actual_values = [t.value for t in tokens]
    assert actual_values == expected_values


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


if __name__ == "__main__":
    pytest.main()
