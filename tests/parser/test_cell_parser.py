# Set output for parser debugging before importing Parser classes.
# from sly import Parser as SlyParser
# SlyParser.debugfile = "sly-debug.out"
from __future__ import annotations

import pytest

import mckit.parser.cell_parser as clp

from mckit.body import Body
from mckit.material import Material
from mckit.parser.common import (
    CellDummyIndex,
    CellStrictIndex,
    CompositionStrictIndex,
    DummyComposition,
    DummyMaterial,
    DummySurface,
    SurfaceDummyIndex,
    SurfaceStrictIndex,
)
from mckit.transformation import Transformation
from mckit.utils.indexes import Index


def create_cell(
    cell_no: int,
    geometry: list,
    material: Material | None = None,
    transformation: Transformation | None = None,
    **options,
):
    if not options:
        options = {}
    options["name"] = cell_no

    def convert_integers_to_surfaces(_geometry):
        for i, e in enumerate(_geometry):
            if isinstance(e, int):
                _geometry[i] = DummySurface(e)
            elif isinstance(e, list):
                convert_integers_to_surfaces(e)

    convert_integers_to_surfaces(geometry)

    if material:
        options["MAT"] = material
    if transformation:
        options["TRCL"] = transformation

    return Body(geometry, **options)


@pytest.mark.parametrize(
    "text,expected_types,expected_values",
    [
        ("1 0", ["INTEGER", "ZERO"], [1, 0]),
        ("1 1 -0.083", ["INTEGER", "INTEGER", "FLOAT"], [1, 1, -0.083]),
    ],
)
def test_cell_lexer(text, expected_types, expected_values):
    lexer = clp.Lexer()
    tokens = list(lexer.tokenize(text))
    actual_types = [f.type for f in tokens]
    actual_values = [f.value for f in tokens]
    assert actual_types == expected_types
    assert actual_values == expected_values


@pytest.mark.parametrize(
    "text,expected,surfaces",
    [
        ("1 0 1", create_cell(1, [1]), [1]),
        ("1 0 -1", create_cell(1, [1, "C"]), [1]),
        ("1 0 1 2", create_cell(1, [1, 2, "I"]), [1, 2]),
        ("1 0 1 -2", create_cell(1, [1, 2, "C", "I"]), [1, 2]),
        ("1 0 1  2 -3", create_cell(1, [1, 2, "I", 3, "C", "I"]), [1, 2, 3]),
        ("1 0 (1  2) : 3", create_cell(1, [1, 2, "I", 3, "U"]), [1, 2, 3]),
        (
            "1 0 (1  2) : (3 4)",
            create_cell(1, [1, 2, "I", 3, 4, "I", "U"]),
            [1, 2, 3, 4],
        ),
    ],
)
def test_parser_geometry(text, expected, surfaces):
    surfaces_index = create_dummy_surface_index(surfaces)
    actual = clp.parse(text, surfaces=surfaces_index)
    expected.options["original"] = text
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected,surfaces,compositions",
    [
        (
            "1 1 -1.0 1",
            create_cell(1, [1], material=DummyMaterial(1, density=1.0)),
            [1],
            [1],
        ),
        (
            "1 1 .08 1",
            create_cell(1, [1], material=DummyMaterial(1, concentration=0.08)),
            [1],
            [1],
        ),
    ],
)
def test_parser_with_materials(text, expected, surfaces, compositions):
    surfaces_index = create_dummy_surface_index(surfaces)
    composition_index = create_dummy_composition_index(compositions)
    actual = clp.parse(text, surfaces=surfaces_index, compositions=composition_index)
    expected.options["original"] = text
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected,surfaces",
    [
        ("1 0 1 IMP:n=1.0", create_cell(1, [1], IMPN=1.0), [1]),
        ("1 0 1 vol 1.0", create_cell(1, [1], VOL=1.0), [1]),
        ("1 0 1 U=200 PMT=0", create_cell(1, [1], U=200, PMT=0), [1]),
    ],
)
def test_parser_with_attributes(text, expected, surfaces):
    surfaces_index = create_dummy_surface_index(surfaces)
    actual = clp.parse(text, surfaces=surfaces_index)
    expected.options["original"] = text
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected,surfaces,cells",
    [
        (
            "2 like 1 but imp:p=2.0",
            create_cell(2, [1], IMPN=1.0, IMPP=2.0),
            [1],
            [create_cell(1, [1], IMPN=1.0)],
        )
    ],
)
def test_parser_with_like_spec(text, expected, surfaces, cells):
    surfaces_index = create_dummy_surface_index(surfaces)
    cells_index = CellStrictIndex.from_iterable(cells)
    actual = clp.parse(text, cells=cells_index, surfaces=surfaces_index)
    expected.options["original"] = text
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            """93    0   (
            16 24
          )
C
          (
            -565:+563
          )
        """,
            93,
        )
    ],
)
def test_found_failures(text, expected):
    surfaces_index = SurfaceDummyIndex()
    cells_index = CellDummyIndex()
    actual = clp.parse(text, cells=cells_index, surfaces=surfaces_index)
    assert actual is not None
    assert actual.name() == expected


def create_dummy_surface_index(surfaces: list[int]) -> Index:
    return SurfaceStrictIndex.from_iterable(map(DummySurface, surfaces))


def create_dummy_composition_index(compositions: list[int]) -> Index:
    return CompositionStrictIndex.from_iterable(map(DummyComposition, compositions))


if __name__ == "__main__":
    pytest.main()
