from __future__ import annotations

from collections.abc import Iterable

from mckit.surface import EX, Plane, Surface
from mckit.utils.indexes import Index, NumberedItemNotFoundError


class DummySurface(Plane):
    """Dummy surface to substitute surface when it's not found in a ``IgnoringIndex``."""

    def __init__(self, name: int):
        super().__init__(EX, 0.0, name=name, comment="dummy")

    def __str__(self) -> str:
        return str(self.name())

    def __repr__(self):
        return f"DummySurface({self.name()})"


def raise_on_absent_surface_strategy(name: int) -> DummySurface | None:
    raise SurfaceNotFoundError(name)


def dummy_on_absent_surface_strategy(name: int) -> DummySurface | None:
    return DummySurface(name)


class SurfaceStrictIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(raise_on_absent_surface_strategy, **kwargs)

    @classmethod
    def from_iterable(cls, items: Iterable[Surface]) -> SurfaceStrictIndex:
        index = cls()
        index.update((c.name(), c) for c in items)
        return index


class SurfaceDummyIndex(Index):
    def __init__(self, **kwargs):
        super().__init__(dummy_on_absent_surface_strategy, **kwargs)


class SurfaceNotFoundError(NumberedItemNotFoundError):
    kind = "Surface"
