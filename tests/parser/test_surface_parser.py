from __future__ import annotations

import pytest

import mckit.parser.common.transformation_index as ti
import mckit.parser.common.utils as cmn
import mckit.parser.surface_parser as srp

from mckit.surface import create_surface
from mckit.utils.indexes import IgnoringIndex


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 PX 0", create_surface("PX", 0.0, name=1)),
        (
            "*1 P 1.5 1.4 1.3 1.2",
            create_surface("P", 1.5, 1.4, 1.3, 1.2, name=1, modifier="*"),
        ),
        (
            """
    158214   RPP  +558.364973080895990 +902.003588792269060  &
              -428.589771011879980 -105.426621291914000  &
              +438.709115982056010 +662.547063827514990
         """,
            create_surface(
                "RPP",
                558.364973080895990,
                902.003588792269060,
                -428.589771011879980,
                -105.426621291914000,
                438.709115982056010,
                662.547063827514990,
                name=158214,
            ),
        ),
    ],
)
def test_good_path(text, expected):
    actual = srp.parse(text)
    assert actual.mcnp_words() == expected.mcnp_words()


# noinspection PyTypeChecker
@pytest.mark.parametrize("text, expected", [("1 2 PX 0", create_surface("PX", 0.0))])
def test_absent_transformation_with_ignore_strategy(text, expected):
    actual = srp.parse(text, transformations=IgnoringIndex())
    assert actual == expected
    assert "transform" not in actual.options


@pytest.mark.parametrize("text,msg_contains", [("1 2 PX 0", 2)])
def test_absent_surface_with_raise_strategy(text, msg_contains):
    with pytest.raises(KeyError, match=f"Transformation #{msg_contains} is not found"):
        srp.parse(text, transformations=ti.TransformationStrictIndex())


# noinspection PyTypeChecker
@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 2 PX 0.1", create_surface("PX", 0.1, transform=ti.DummyTransformation(2))),
        (
            "1 1 SX 4 +5.0",
            create_surface("SX", 4, 5.0, name=1, transform=ti.DummyTransformation(1)),
        ),
    ],
)
def test_absent_surface_with_dummy_strategy(text, expected):
    actual = srp.parse(text, transformations=ti.TransformationDummyIndex())
    assert actual == expected


@pytest.mark.parametrize(
    "text,msg",
    [
        ("kjk", "Surface specification must start with"),
        ("*1 P", "Surface parameters are not specified in '\\*1 P'"),
        ("1 2 NN", "NN is not a valid surface type"),
    ],
)
def test_bad_surface_spec(text, msg):
    with pytest.raises(cmn.ParseError, match=msg):
        srp.parse(text)


if __name__ == "__main__":
    pytest.main()
