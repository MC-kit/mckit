from __future__ import annotations

from collections.abc import Iterable

from mckit.body import GLOBAL_BOX, Body, Card
from mckit.constants import MIN_BOX_VOLUME
from mckit.utils.indexes import Index, NumberedItemNotFoundError


class DummyCell(Body):
    """To substitute cell when it's not found."""

    def __init__(self, name: int):
        self._name = name
        options = {"name": name, "comment": "dummy"}
        Card.__init__(self, **options)

    def __hash__(self):
        return Card.__hash__(self)

    def __eq__(self, other):
        return Card.__eq__(self, other)

    def is_equivalent_to(self, other):
        return self.name() == other.name()

    @property
    def shape(self):
        raise NotImplementedError("The method is not available in dummy object")

    def intersection(self, other):
        raise NotImplementedError("The method is not available in dummy object")

    def union(self, other):
        raise NotImplementedError("The method is not available in dummy object")

    def simplify(
        self,
        box=GLOBAL_BOX,
        split_disjoint=False,
        min_volume=MIN_BOX_VOLUME,
        trim_size=1,
    ):
        raise NotImplementedError("The method is not available in dummy object")

    def fill(self, universe=None, recurrent=False, simplify=False, **kwargs):
        raise NotImplementedError("The method is not available in dummy object")

    def transform(self, tr):
        raise NotImplementedError("The method is not available in dummy object")


def raise_on_absent_cell_strategy(name: int) -> DummyCell | None:
    raise CellNotFoundError(name)


def dummy_on_absent_cell_strategy(name: int) -> DummyCell | None:
    return DummyCell(name)


class CellStrictIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(raise_on_absent_cell_strategy, **kwargs)

    @classmethod
    def from_iterable(cls, items: Iterable[Body]) -> CellStrictIndex:
        index = cls()
        index.update((c.name(), c) for c in items)
        return index


class CellDummyIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(dummy_on_absent_cell_strategy, **kwargs)


class CellNotFoundError(NumberedItemNotFoundError):
    kind = "Cell"
