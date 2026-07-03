"""Methods to extract cells matching given predicates."""

from __future__ import annotations

from typing import cast

from collections.abc import Callable, Container, Iterable
from itertools import tee
from pathlib import Path

from mckit import Body, Universe
from mckit.parser import from_file
from mckit.utils.named import default_name_key, map_names

BodyPredicate = Callable[[Body], bool]


def filter_by_cell_number(cell_number: int) -> BodyPredicate:
    """Create filter to extract a cell with the given cell number.

    Parameters
    ----------
    cell_number
        cell number to select

    Returns
    -------
        predicate to use in :func:`~mckit.workflow.extract_cells`
    """

    def _call(c: Body) -> bool:
        return cast(int, c.name()) == cell_number

    return _call


def filter_by_cell_numbers(cell_numbers_to_select: Container[int]) -> BodyPredicate:
    """Create filter to extract cells with given numbers.

    Parameters
    ----------
    cell_numbers_to_select
        collection of numbers to select

    Returns
    -------
        predicate to use in :func`~mckit.workflow.extract_cells`
    """

    def _call(c: Body) -> bool:
        return cast(int, c.name()) in cell_numbers_to_select

    return _call


def filter_by_surface_number(surface_number: int) -> BodyPredicate:
    """Create filter to extract cells having a surfaces with the given number.

    Parameters
    ----------
    surface_numbers
        collection of numbers to select

    Returns
    -------
        predicate to use in :func:`~mckit.workflow.extract_cells.extract_cells`
    """

    def _call(c: Body) -> bool:
        return any(n == surface_number for n in map_names(c.shape.get_surfaces()))  # ty:ignore[unresolved-attribute]

    return _call


def filter_by_surface_numbers(surface_numbers_to_select: Container[int]) -> BodyPredicate:
    """Create filter to extract cells having surfaces with given numbers.

    Parameters
    ----------
    surface_numbers_to_select
        collection of numbers to select

    Returns
    -------
        predicate to use in :func:`~mckit.workflow.extract_cells.extract_cells`
    """

    def _call(c: Body) -> bool:
        return any(n in surface_numbers_to_select for n in map_names(c.shape.get_surfaces()))  # ty:ignore[unresolved-attribute]

    return _call


def extract_cells_from_file(
    model_path: str | Path, predicate: BodyPredicate, *, add_surface_sharing_cells: bool = True
) -> set[Body]:
    """Extract cells from a model matching to a predicate.

    Parameters
    ----------
    model_path
        Path to the model file
    predicate
        Method to filter bodies
    add_surface_sharing_cells
        Whether to add surface sharing cells

    Returns
    -------
        Set of the selected cells (Body objects)
    """
    universe = from_file(model_path).universe
    return extract_cells(universe, predicate, add_surface_sharing_cells=add_surface_sharing_cells)


def extract_cells(
    cells: Iterable[Body], predicate: BodyPredicate, *, add_surface_sharing_cells: bool = True
) -> set[Body]:
    """Extract cells matching to `predicate` along with sharing surfaces cells.

    By "sharing surfaces" cells we mean cells sharing some surfaces with
    the cells selected by predicate.

    Parameters
    ----------
    cells
        collection of Body objects to extract from
    predicate
        method to check a Body object
    add_surface_sharing_cells
        Whether to add surface sharing cells

    Returns
    -------
        Set of the selected cells (Body objects)
    """
    it1, it2 = tee(cells)
    selected_cells = set(filter(predicate, it1))

    if add_surface_sharing_cells:
        selected_surfaces: set[int] = set()

        for c in selected_cells:
            selected_surfaces.update(map_names(c.shape.get_surfaces()))  # ty:ignore[unresolved-attribute]

        def _select_adjacent_cells(_c: Body) -> bool:
            return _c.name() not in selected_cells and any(
                cast(int, s.name()) in selected_surfaces
                for s in _c.shape.get_surfaces()  # ty:ignore[unresolved-attribute]
            )

        selected_cells.update(filter(_select_adjacent_cells, it2))

    return selected_cells


def make_universe(cells: Iterable[Body]) -> Universe:
    """Create a Universe instance from collection of cells.

    Parameters
    ----------
    cells
        collection

    Returns
    -------
        Universe object with cells sorted by name.
    """
    return Universe(
        sorted(
            cells,
            key=cast(Callable[[Body], int], cast(object, default_name_key)),
        )
    )
