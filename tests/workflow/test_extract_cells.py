from __future__ import annotations

import pytest

from mckit.utils.named import map_names
from mckit.utils import path_resolver
from mckit.workflow import (
    extract_cells_from_file,
    filter_by_cell_numbers,
    filter_by_surface_numbers,
    make_universe,
)

UNIVERSES_DIR = path_resolver("tests")("universe_test_data")


@pytest.mark.parametrize("universe,select,expected", [("universe1.i", [1], [1, 3])])
def test_extract_by_cell_numbers(universe, select, expected) -> None:
    path = UNIVERSES_DIR / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = extract_cells_from_file(path, filter_by_cell_numbers(select))
    assert set(map_names(actual)) == set(expected)


@pytest.mark.parametrize(
    "universe,select,expected,assc",
    [
        ("universe1.i", [3], [1, 2, 3, 4], True),
        ("universe1.i", [3], [2, 3], False),
    ],
)
def test_extract_by_surface_numbers(universe, select, expected, assc) -> None:
    path = UNIVERSES_DIR / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = extract_cells_from_file(
        path, filter_by_surface_numbers(set(select)), add_surface_sharing_cells=assc
    )
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected
