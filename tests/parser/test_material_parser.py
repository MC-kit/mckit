from __future__ import annotations

import pytest

import mckit.parser.material_parser as mp

from mckit.material import Composition, Element


@pytest.mark.parametrize(
    "text, expected_types, expected_values",
    [
        ("1001.21c -1.0", ["FRACTION"], [(1001, "21c", -1.0)]),
        ("  M100 1000 1.0", ["NAME", "FRACTION"], [100, (1000, None, 1.0)]),
        (
            "  M100 1000 1.0 gas=1",
            ["NAME", "FRACTION", "OPTION"],
            [100, (1000, None, 1.0), "gas=1"],
        ),
        ("M17    18000.70c 1.", ["NAME", "FRACTION"], [17, (18000, "70c", 1.0)]),
    ],
)
def test_composition_lexer(text, expected_types, expected_values):
    lexer = mp.Lexer()
    tokens = list(lexer.tokenize(text))
    result = [t.type for t in tokens]
    assert result == expected_types
    result = [t.value for t in tokens]
    assert result == expected_values


# M17    18000.70c 1. $Ar 00 weight(%)  100


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            """m1
        1001.21c -1.0
        """,
            Composition(weight=[(1001, 1.0)], name=1),
        ),
        (
            """m1000
        1001.21c -1.0 $ eol comment
        """,
            Composition(
                weight=[
                    (
                        Element(
                            1001,
                            lib="21c",
                            # comment="$ eol comment"
                        ),
                        1.0,
                    )
                ],
                name=1000,
            ),
        ),
        (
            """M1000
        1001.21c -1.0
            $ trailing comment1
            $ trailing comment2
        """,
            Composition(
                weight=[(Element(1001, lib="21c"), 1.0)],
                name=1000,
                # comment=["trailing comment1", "trailing comment2"],
            ),
        ),
        (
            """M1000
    1001.21c -1.0
c something
        $ trailing comment1
        $ trailing comment2
        """,
            Composition(
                weight=[(Element(1001, lib="21c"), 1.0)],
                name=1000,
                # comment=["trailing comment1", "trailing comment2"],
            ),
        ),
        (
            """M1000
        1001.21c -1.0
            gas 1
            $ trailing comment1
            $ trailing comment2
        """,
            Composition(
                weight=[(Element(1001, lib="21c"), 1.0)],
                name=1000,
                # comment=["trailing comment1", "trailing comment2"],
                GAS=1,
            ),
        ),
        (
            "m1 1001 0.1 1002 0.9",
            Composition(atomic=[(1001, 0.1), (1002, 0.9)], name=1),
        ),
        (
            "m3 1001 0.1 1002 0.9 gas=1",
            Composition(atomic=[(1001, 0.1), (1002, 0.9)], name=3, GAS=1),
        ),
    ],
)
def test_composition_parser(text, expected):
    result = mp.parse(text)
    assert isinstance(result, Composition), "Parser should create instance of Composition"
    assert result == expected
    assert result.options == expected.options


if __name__ == "__main__":
    pytest.main()
