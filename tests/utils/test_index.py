from __future__ import annotations

from typing import NoReturn

import pytest

from mckit.utils.indexes import Index


def dummy_strategy(c: int) -> int:
    return c * c


@pytest.mark.parametrize("inp", [{1: 1, 2: 4}, {}])
def test_index_with_dummy_strategy(inp: dict[int, int]) -> None:
    dictionary = Index(dummy_strategy)
    dictionary.update(inp)
    for k in range(5):
        v = dictionary[k]
        expected = k * k
        assert expected == v


class MyKeyError(KeyError):
    def __init__(self, key: int, *args, **kwargs):
        super().__init__(args, kwargs)
        self._key = key

    @property
    def key(self):
        return self._key


def strict_strategy(c: int) -> NoReturn:
    raise MyKeyError(c)


@pytest.mark.parametrize(
    "inp,keys,success",
    [({1: 1, 2: 4}, [1, 2, 3], [True, True, False]), ({}, [1], [False])],
)
def test_index_with_strict_strategy(
    inp: dict[int, int], keys: list[int], success: list[bool]
) -> None:
    dictionary = Index(strict_strategy)
    dictionary.update(inp)
    for k, s in zip(keys, success, strict=False):
        if s:
            assert dictionary[k]
        else:
            with pytest.raises(MyKeyError):
                _ = dictionary[k]
