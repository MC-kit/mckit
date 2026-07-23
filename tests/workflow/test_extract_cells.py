from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

import pytest

from mckit import from_file
from mckit.utils.named import map_names
from mckit.workflow import (
    extract_cells,
    extract_cells_from_file,
    filter_and,
    filter_by_cell_number,
    filter_by_cell_numbers,
    filter_by_comment,
    filter_by_shared_surfaces,
    filter_by_surface_number,
    filter_by_surface_numbers,
    filter_not,
    filter_or,
    make_universe,
)

if TYPE_CHECKING:
    from mckit import Universe


@pytest.fixture(scope="session")
def universe_test_data(data: Path) -> Path:
    return data / "universe"


@pytest.fixture(scope="session")
def universe1(universe_test_data) -> Universe:
    path = universe_test_data / "universe1.i"
    assert path.exists(), f"Cannot find path {path}"
    return from_file(path).universe


@pytest.mark.parametrize("universe,select,expected", [("universe1.i", 1, [1])])
def test_extract_by_cell_number(universe, select, expected, universe_test_data: Path) -> None:
    path = universe_test_data / universe
    assert path.exists(), f"Cannot find path {path}"
    actual = extract_cells_from_file(path, filter_by_cell_number(select))
    assert set(map_names(actual)) == set(expected)


@pytest.mark.parametrize("select,expected", [([1], [1]), ([2], [2])])
def test_extract_by_cell_numbers(select, expected, universe1) -> None:
    actual = extract_cells(universe1, filter_by_cell_numbers(select))
    assert set(map_names(actual)) == set(expected)


@pytest.mark.parametrize("select1, select2, select_not, expected", [([1, 2], [2, 3], [2], [1, 3])])
def test_filter_compositions(select1, select2, select_not, expected, universe1) -> None:
    actual = extract_cells(
        universe1,
        filter_and(
            filter_or(filter_by_cell_numbers(select1), filter_by_cell_numbers(select2)),
            filter_not(filter_by_cell_numbers(select_not)),
        ),
    )
    assert set(map_names(actual)) == set(expected)


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "select,expected",
    [
        (3, [2, 3]),
        (2, [2, 3]),
    ],
)
def test_extract_by_surface_number(select, expected, universe1) -> None:
    actual = list(extract_cells(universe1, filter_by_surface_number(select)))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "select,expected",
    [
        (3, [1, 2, 4]),
        (2, [3]),
    ],
)
def test_extract_by_shared_surfaces(select: int, expected: list[int], universe1: Universe) -> None:
    selected_cells = list(extract_cells(universe1, filter_by_cell_number(select)))
    actual = list(extract_cells(universe1, filter_by_shared_surfaces(selected_cells)))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "select,expected",
    [
        ([3], [2, 3]),
    ],
)
def test_extract_by_surface_numbers(select, expected, universe1) -> None:
    actual = list(extract_cells(universe1, filter_by_surface_numbers(set(select))))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected


@pytest.mark.parametrize(
    "comment,expected",
    [
        ("sphere", [1]),
        ("cylinder", [2]),
    ],
)
def test_extract_by_comment(comment, expected, universe1) -> None:
    actual = list(extract_cells(universe1, filter_by_comment(comment)))
    assert set(map_names(actual)) == set(expected)
    new_universe = make_universe(actual)
    assert len(new_universe) == len(expected)
    assert list(map_names(new_universe)) == expected
