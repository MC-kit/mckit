from __future__ import annotations

import pytest

import mckit.parser.material_parser as mp

from mckit.material import Composition, Element


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


def test_material_with_ampersand(data):
    inp = data / "parser/material-with-ampersands.txt"
    actual = mp.parse(inp.read_text(encoding="utf8"))
    assert isinstance(actual, Composition), "Parser should create instance of Composition"
    assert actual.name() == 8902
    assert len(actual) == 34


def test_bad_spec() -> None:
    with pytest.raises(ValueError, match="Material definition must start with"):
        mp.parse("xxx")
