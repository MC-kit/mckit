from __future__ import annotations

from pathlib import Path

import pytest

from mckit.utils.named import map_names
from mckit.workflow import (
    extract_cells_from_file,
    filter_by_cell_number,
    filter_by_cell_numbers,
    filter_by_surface_number,
    filter_by_surface_numbers,
    make_universe,
)


@pytest.fixture(scope="session")
def universe_test_data(data: Path) -> Path:
    return data / "universe"


@pytest.mark.parametrize("universe,select,expected", [("universe1.i", 1, [1, 3])])
def test_extract_by_cell_number(universe, select, expected, universe_test_data: Path) -> None:
    path = universe_test_data / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = extract_cells_from_file(path, filter_by_cell_number(select))
    assert set(map_names(actual)) == set(expected)


@pytest.mark.parametrize("universe,select,expected", [("universe1.i", [1], [1, 3])])
def test_extract_by_cell_numbers(universe, select, expected, universe_test_data: Path) -> None:
    path = universe_test_data / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = extract_cells_from_file(path, filter_by_cell_numbers(select))
    assert set(map_names(actual)) == set(expected)


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "universe,select,expected,assc",
    [
        ("universe1.i", 3, [1, 2, 3, 4], True),
        ("universe1.i", 3, [2, 3], False),
    ],
)
def test_extract_by_surface_number(universe, select, expected, assc, universe_test_data) -> None:
    path = universe_test_data / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = list(extract_cells_from_file(
        path, filter_by_surface_number(select), add_surface_sharing_cells=assc
    ))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "universe,select,expected,assc",
    [
        ("universe1.i", [3], [1, 2, 3, 4], True),
        ("universe1.i", [3], [2, 3], False),
    ],
)
def test_extract_by_surface_numbers(universe, select, expected, assc, universe_test_data) -> None:
    path = universe_test_data / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = list(extract_cells_from_file(
        path, filter_by_surface_numbers(set(select)), add_surface_sharing_cells=assc
    ))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected
