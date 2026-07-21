"""Methods to extract cells matching given predicates."""

from __future__ import annotations

from typing import cast, Generator

from collections.abc import Callable, Container, Iterable
from itertools import chain
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
    surface_number
        the number to select

    Returns
    -------
        predicate to use in :func:`~mckit.workflow.extract_cells.extract_cells`
    """

    def _call(c: Body) -> bool:
        return any(n == surface_number for n in map_names(c.shape.scan_surfaces()))  # ty:ignore[unresolved-attribute]

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
        return any(n in surface_numbers_to_select for n in map_names(c.shape.scan_surfaces()))  # ty:ignore[unresolved-attribute]

    return _call

def filter_by_comment(text: str) -> BodyPredicate:
    """Select cells containing the text in trailing comment.

    Parameters
    ----------
    text
        what to search in the cell's comment

    Returns
    -------
    if the cell has comment, and it contains the text

    """
    def _call(cell: Body)->bool:
        comment = cell.options.get("comment")
        if not comment:
            return False
        return any(lambda x: text in x and (print(text, "in", x) or True) for x in comment)
    return _call

def extract_cells_from_file(
    model_path: str | Path, predicate: BodyPredicate, *, add_surface_sharing_cells: bool = True
) -> Generator[Body]:
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
    yield from extract_cells(universe, predicate, add_surface_sharing_cells=add_surface_sharing_cells)


def extract_cells(
    cells: Iterable[Body], predicate: BodyPredicate, *, add_surface_sharing_cells: bool = True
) -> Generator[Body]:
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
    if add_surface_sharing_cells:
        selected_cells = list(filter(predicate, cells))
        yield from selected_cells
        selected_cells_names = set(map_names(selected_cells))
        selected_surfaces: set[int] = set(chain(*(map_names(c.shape.scan_surfaces()) for c in selected_cells)))


        def _select_adjacent_cells(_c: Body) -> bool:
            return _c.name() not in selected_cells_names and any(
                cast(int, s.name()) in selected_surfaces
                for s in _c.shape.scan_surfaces()
            )

        yield from filter(_select_adjacent_cells, cells)
    else:
        yield from filter(predicate, cells)



def make_universe(cells: Iterable[Body]) -> Universe:
    """Create a Universe instance from iterable collection of cells.

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
