from __future__ import annotations

from collections.abc import Iterable

from mckit.material import Composition, Material
from mckit.utils.indexes import Index, NumberedItemNotFoundError


class DummyMaterial(Material):
    def __init__(
        self,
        name: int,
        *,
        density: float | None = None,
        concentration: float | None = None,
    ) -> None:
        if (density is None) == (concentration is None):
            msg = "Specify only one of the parameters"
            raise ValueError(msg)
        if density is None:
            # noinspection PyTypeChecker
            super().__init__(
                composition=DummyComposition(name), concentration=concentration * 1.0e24
            )
        else:
            super().__init__(composition=DummyComposition(name), density=density)


# noinspection PyTypeChecker
class DummyComposition(Composition):
    """To substitute composition when it's not found."""

    def __init__(self, name: int):
        super().__init__(name=name, weight=[(1001, 1.0)], comment="dummy")


def raise_on_absent_composition_strategy(name: int) -> DummyComposition | None:
    raise CompositionNotFoundError(name)


def dummy_on_absent_composition_strategy(name: int) -> DummyComposition | None:
    return DummyComposition(name)


class CompositionStrictIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(raise_on_absent_composition_strategy, **kwargs)

    @classmethod
    def from_iterable(cls, items: Iterable[Composition]) -> CompositionStrictIndex:
        index = cls()
        index.update((c.name(), c) for c in items)
        return index


class CompositionDummyIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(dummy_on_absent_composition_strategy, **kwargs)


class CompositionNotFoundError(NumberedItemNotFoundError):
    kind = "Composition"
