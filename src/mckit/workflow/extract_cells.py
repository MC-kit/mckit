"""Methods to extract cells matching given predicates."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import re

from collections.abc import Callable
from itertools import chain
from pathlib import Path

from mckit import Body, Universe
from mckit.parser import from_file
from mckit.utils.named import default_name_key, map_names

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Iterator

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
        return any(n == surface_number for n in map_names(c.shape.scan_surfaces()))

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
        return any(n in surface_numbers_to_select for n in map_names(c.shape.scan_surfaces()))

    return _call


def filter_by_comment(predicate: str | re.Pattern | Callable[[str], bool]) -> BodyPredicate:
    """Select cells containing the text in trailing comment.

    Parameters
    ----------
    predicate
        what to search in the cell's comment

    Returns
    -------
    Function searching predicate in a cell comment

    """

    def _call(cell: Body) -> bool:
        """Search predicate in comment.

        Parameters
        ----------
        cell
            to check

        Returns
        -------
        if the cell comment matches predicate
        """
        return cell.match_comment(predicate)

    return _call


def filter_by_shared_surfaces(selected_cells: Iterable[Body]) -> BodyPredicate:
    """Select cells containing the text in trailing comment.

    Parameters
    ----------
    selected_cells
        preliminary selected

    Returns
    -------
    Function checking if a cell uses any surfaces as selected cells

    """
    selected_cells_names: set[int] = set(map_names(selected_cells))
    selected_surfaces: set[int] = set(
        chain(*(map_names(c.shape.scan_surfaces()) for c in selected_cells))
    )

    def _call(cell: Body) -> bool:
        """Check if the cell uses surfaces from selected cells.

        Parameters
        ----------
        cell
            to check

        Returns
        -------
        if there are shared surfaces with surfaces used in preliminary selected cells.
        """
        return cell.name() not in selected_cells_names and any(
            cast(int, s.name()) in selected_surfaces for s in cell.shape.scan_surfaces()
        )

    return _call

def filter_not(predicate: BodyPredicate) -> BodyPredicate:
    """Compose negation to the predicate.

    Parameters
    ----------
    predicate
        what to negate

    Returns
    -------
    Negative to given predicate.
    """
    def _call(cell: Body)->bool:
        return not predicate(cell)
    return _call

def filter_or(*predicates: BodyPredicate) -> BodyPredicate:
    """Compose "OR" expression from given predicates.

    Parameters
    ----------
    predicates
        to form expression

    Returns
    -------
    "OR" expression of the predicates
    """
    def _call(cell: Body)->bool:
        return any(p(cell) for p in predicates)
    return _call

def filter_and(*predicates: BodyPredicate) -> BodyPredicate:
    """Compose "AND" expression from given predicates.

    Parameters
    ----------
    predicates
        to form expression

    Returns
    -------
    "AND" expression of the predicates
    """

    def _call(cell: Body)->bool:
        return all(p(cell) for p in predicates)
    return _call


def extract_cells_from_file(model_path: str | Path, predicate: BodyPredicate) -> Iterable[Body]:
    """Extract cells from a model matching to a predicate.

    Parameters
    ----------
    model_path
        Path to the model file
    predicate
        Method to filter bodies

    Returns
    -------
    Iterable over the selected cells (Body objects)
    """
    universe = from_file(model_path).universe
    return extract_cells(universe, predicate)


def extract_cells(cells: Iterable[Body], predicate: BodyPredicate) -> Iterator[Body]:
    """Extract cells matching to `predicate` along with sharing surfaces cells.

    By "sharing surfaces" cells we mean cells sharing some surfaces with
    the cells selected by predicate.

    Parameters
    ----------
    cells
        collection of Body objects to extract from
    predicate
        method to check a Body object

    Returns
    -------
    Iterator over the selected cells (Body objects)
    """
    return filter(predicate, cells)


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
