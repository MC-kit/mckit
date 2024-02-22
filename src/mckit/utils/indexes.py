"""Classes to index MCNP objects on model file parsing."""

from __future__ import annotations

from typing import Callable, Optional, TypeVar

from collections.abc import Iterable
from functools import reduce

from mckit.utils.named import Name, default_name_key

Key = TypeVar("Key")
Item = TypeVar("Item")
FactoryMethodWithKey = Callable[[Key], Optional[Item]]


class Index(dict[Key, Item]):
    """Like collections.defaultdict but the factory takes key as argument.

    The class redefines __missing__ method to use `key` on calling factory method.

    Attrs:
        _default_factory (FactoryMethodWithKey):
            Same as in Args.
    """

    def __init__(
        self,
        default_factory: FactoryMethodWithKey | None = None,
        **kwargs: dict[Key, Item],
    ) -> None:
        """Create `Index`.

        Args:
            default_factory: factory method accepting `key` as the only positional argument.
            kwargs: keyword arguments to pass to base class, if any
        """
        super().__init__(self, **kwargs)
        self._default_factory = default_factory

    @property
    def default_factory(self) -> FactoryMethodWithKey | None:
        """Public accessor to `self._default_factory`."""
        return self._default_factory

    def __missing__(self, key: Key) -> Item | None:
        """Calls default factory with the key as argument."""
        if self._default_factory:
            return self._default_factory(key)

        raise NumberedItemNotFoundError(key)


# noinspection PyUnusedLocal
def ignore(_: Key) -> Item | None:
    """Default factory for `IgnoringIndex`.

    Returns:
        None - always.
    """
    return None


class IgnoringIndex(Index[Key, Item]):
    """Index ignoring absence of a key in the dictionary."""

    def __init__(self, **kwargs: dict[Key, Item]) -> None:
        Index.__init__(self, ignore, **kwargs)


class NumberedItemNotFoundError(KeyError):
    """Error to raise, when an item is not found in an `Index`."""

    kind: str = ""

    def __init__(self, key: Key) -> None:
        self._key = key
        super().__init__(f"{self.kind} #{self._key} is not found")


class NumberedItemDuplicateError(ValueError):
    """Error to raise, when an item has duplicate in an `Index`."""

    kind: str = ""

    def __init__(self, key: Key, prev: Item, curr: Item) -> None:
        self._key = key
        self._prev = prev
        self._curr = curr
        super().__init__(
            f"{self.kind} #{self._key} is duplicated, see {self._prev} and {self._curr}"
        )


def raise_on_duplicate_strategy(key: Key, prev: Item, curr: Item) -> None:
    """Raise error on `key` duplicate found, regardless values.

    Args:
        key: a key in `Index`.
        prev: the value already in `Index`.
        curr: the new value to add to `Index`.

    Raises:
        NumberedItemDuplicateError: exception to inform on `key`, `prev` and `curr` values.
    """
    raise NumberedItemDuplicateError(key, prev, curr)


def ignore_equal_objects_strategy(key: Key, prev: Item, curr: Item) -> None:
    """Raise error on `key` duplicate found, if the values are not equal.

    Otherwise, ignore an attempt to add the same key/value pair.

    Args:
        key: a key in `Index`.
        prev: the value already in `Index`.
        curr: the new value to add to `Index`.

    Raises:
        NumberedItemDuplicateError: exception to inform on `key`, `prev` and `curr` values.
    """
    if prev is not curr and prev != curr:
        raise NumberedItemDuplicateError(key, prev, curr)


class StatisticsCollector(dict[Key, int]):
    """Duplicates counter."""

    def __init__(self, ignore_equal=False):
        super().__init__(self)
        self.ignore_equal = ignore_equal

    def __missing__(self, key):
        return 1

    def __call__(self, key: Key, prev: Item, curr: Item) -> None:
        """Increase counter.

        If items are duplicates and `self.ignore_equal` is set on,
        then skip.

        Args:
            key: a key in `StatisticsCollector`.
            prev: the value already in `StatisticsCollector`.
            curr: the new value to add to `StatisticsCollector`.
        """
        if not self.ignore_equal or prev != curr:
            self[key] += 1


class IndexOfNamed(Index[Key, Item]):
    """Index of items from a key can be extracted."""

    @classmethod
    def from_iterable(
        cls: type[IndexOfNamed[Key, Item]],
        items: Iterable[Item],
        *,
        key: Callable[[Item], Name] = default_name_key,
        default_factory: Callable[[Key], Item] | None = None,
        on_duplicate: Callable[[Key, Item, Item], None] | None = None,
    ) -> IndexOfNamed:
        """Construct `IndexOfNamed` from `items`."""
        index = cls(default_factory)

        def _reducer(a, b):
            name = key(b)
            if on_duplicate is not None and name in a:
                on_duplicate(name, a[name], b)
            a[name] = b
            return a

        return reduce(_reducer, items, index)
