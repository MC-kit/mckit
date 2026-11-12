from __future__ import annotations

import pytest

import mckit.parser.cell_parser as clp
import mckit.parser.common.utils as cmn

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
    expected.original = text
    assert actual == expected


@pytest.mark.parametrize(
    "text, message, surfaces, compositions",
    [
        pytest.param(
            "m1 0 1", "Cell specification must start with a cell number", [], [], id="bad-name"
        ),
        pytest.param("1 x 1", "Cell specification must define material", [], [], id="no-material"),
        pytest.param("1 1.5 1", "Invalid material specification '1.5'", [], [], id="bad-material"),
        pytest.param(
            "1 1", "Composition #1: missed density specification", [], [1], id="no-density"
        ),
        pytest.param(
            "1 0 U=1", "Cell specification must define geometry", [], [], id="no-geometry"
        ),
        pytest.param(
            "1 0 (1",
            "Could not parse cell geometry specification '\\(1'",
            [],
            [],
            id="bad-geometry",
        ),
        pytest.param(
            "1 0 1 U=x",
            "Cell attribute 'U' should be specified with an integer value",
            [1],
            [],
            id="bad-int-attribute",
        ),
        pytest.param(
            "1 0 1 TMP=y",
            "Cell attribute 'TMP' should be specified with a float value",
            [1],
            [],
            id="bad-float-attribute",
        ),
        pytest.param(
            "1 0 1 FCL:N",
            "FCL attribute ':N' should specify a float value",
            [1],
            [],
            id="fcl-no-value",
        ),
        pytest.param(
            "1 0 1 FCL:N,P=1.0",
            "FCL attribute ':N,P=1.0' should specify a single particle",
            [1],
            [],
            id="fcl-many-particles",
        ),
        pytest.param(
            "1 0 1 IMP:N=",
            "IMP attribute ':N=' should specify importance values",
            [1],
            [],
            id="imp-no-values",
        ),
        pytest.param("1 0 1 TRCL=x", "TRCL attribute '=x' is not valid", [1], [], id="bad-trcl"),
        pytest.param(
            "1 0 1 trcl (1 2)",
            "Cell transformation requires a translation vector of 3 numbers",
            [1],
            [],
            id="trcl-short-translation",
        ),
        pytest.param(
            "1 0 1 trcl (1 2 3 4)",
            "Invalid number of transformation rotation parameters: 1",
            [1],
            [],
            id="trcl-short-rotation",
        ),
        pytest.param(
            "1 0 1 trcl (1 0 0 1 0 0 0 1 0 0 0 1 1.5)",
            "The M option should be specified as an integer",
            [1],
            [],
            id="trcl-float-m-option",
        ),
        pytest.param(
            "1 0 1 FILL=x",
            "FILL attribute '=x' should specify a universe number",
            [1],
            [],
            id="bad-fill",
        ),
        pytest.param(
            "1 0 1 LIKE 2 BUT",
            "Misplaced 'LIKE' keyword: a cell can not have both geometry and LIKE",
            [1],
            [],
            id="misplaced-like",
        ),
        pytest.param(
            "1 0 1 BUT",
            "Misplaced 'BUT' keyword: 'BUT' is allowed only after 'LIKE <n> BUT'",
            [1],
            [],
            id="misplaced-but",
        ),
    ],
)
def test_bad_cell_spec(text, message, surfaces, compositions):
    surfaces_index = create_dummy_surface_index(surfaces)
    composition_index = create_dummy_composition_index(compositions)
    with pytest.raises(cmn.ParseError, match=message):
        clp.parse(text, surfaces=surfaces_index, compositions=composition_index)


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
    expected.original = text
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected,surfaces",
    [
        ("1 0 1 IMP:n=1.0", create_cell(1, [1], IMPN=1.0), [1]),
        ("1 0 1 vol 1.0", create_cell(1, [1], VOL=1.0), [1]),
        ("1 0 1 U=200 PMT=0", create_cell(1, [1], U=200, PMT=0), [1]),
        ("1 0 1 U=200 FCL:N=1", create_cell(1, [1], U=200, FCLN=1), [1]),
        (
            "1 0 1 trcl (1 0 0 1 0 0 0 1 0 0 0 1 1)",
            create_cell(
                1,
                [1],
                transformation=Transformation(
                    translation=[1, 0, 0], rotation=[1, 0, 0, 0, 1, 0, 0, 0, 1], inverted=False
                ),
            ),
            [1],
        ),
        (
            "1 0 1 *trcl (-1 0 0  0 90 90  90 0 90  90 90 0)",
            create_cell(
                1,
                [1],
                transformation=Transformation(
                    translation=[-1, 0, 0], rotation=[1, 0, 0, 0, 1, 0, 0, 0, 1], inverted=False
                ),
            ),
            [1],
        ),
    ],
)
def test_parser_with_attributes(text, expected, surfaces):
    surfaces_index = create_dummy_surface_index(surfaces)
    actual = clp.parse(text, surfaces=surfaces_index)
    expected.original = text
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
    expected.original = text
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
