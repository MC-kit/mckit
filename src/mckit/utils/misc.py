"""Generic utility methods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import collections
import collections.abc
import functools
import itertools

from copy import deepcopy

import numpy as np

from numpy import ndarray

from mckit.constants import FLOAT_TOLERANCE

MAX_DIGITS = np.finfo(float).precision

if TYPE_CHECKING:
    from numpy.typing import NDArray

    FloatArray = NDArray[np.floating]
    IntArray = NDArray[np.int_]


def significant_digits(
    value: float, reltol: float = FLOAT_TOLERANCE, resolution: float | None = None
) -> int:
    """The minimum number of significant digits to provide relative tolerance.

    Args:
        value:  The value to be checked.
        reltol: Relative tolerance needed to represent the value.
        resolution:  The threshold value, below which numbers are believed to be zero, optional.

    Returns:
        The number of significant digits.
    """
    if value == 0.0 or (resolution and abs(value) < resolution):
        return 0
    dec = get_decades(value)
    low = min(dec, 0)
    high = MAX_DIGITS
    d = d0 = abs(value)
    while high - low > 1:
        p = round(0.5 * (high + low))
        v = round(value, p)
        d = max(d0, abs(v))
        if abs(value - v) > reltol * d:
            low = p
        else:
            high = p
    v = round(value, low)
    if abs(value - v) < reltol * d:
        return low
    return high


def get_decades(value: float) -> int:
    """Compute number of digits needed to represent integer part of 'value' in fixed format.

    Args:
        value: ... to check

    Returns:
        Number of decades.
    """
    decimal_power = np.log10(abs(float(value))) if value != 0 else 0
    decades = np.trunc(decimal_power)
    if decimal_power < 0:
        decades -= 1
    return int(decades)


def significant_array(
    array: FloatArray, reltol: float = FLOAT_TOLERANCE, resolution: float | None = None
) -> IntArray:
    """Compute the minimum numbers of significant digits to achieve desired tolerance."""
    result = np.empty_like(array, dtype=int)
    for index in zip(*map(np.ravel, np.indices(array.shape)), strict=False):
        value = array[index].item()
        result[index] = significant_digits(value, reltol, resolution)
    return result


def round_scalar(value: float, digits: int | None = None) -> float:
    """Rounds scalar value to represent the value in minimal form.

    Args:
        value: The value to be rounded.
        digits: The number of significant digits, optional.

    Returns:
        Rounded value.
    """
    if digits is None:
        digits = significant_digits(value, FLOAT_TOLERANCE, FLOAT_TOLERANCE)
    return round(value, digits)


def round_array(array: FloatArray, digits_array: IntArray | None = None) -> ndarray:
    """Rounds array to desired precision.

    Args:
        array:   Array of values.
        digits_array:   Array of corresponding significant digits.

    Returns:
        Rounded array.
    """
    if digits_array is None:
        digits_array = significant_array(array, FLOAT_TOLERANCE, FLOAT_TOLERANCE)
    result: ndarray = np.empty_like(array)
    for index in zip(*map(np.ravel, np.indices(array.shape)), strict=False):
        digits: int = digits_array[index].item()
        result[index] = round_scalar(array[index].item(), digits)
    return result


@functools.singledispatch
def are_equal(a, b) -> bool:
    """Check if objects are equal dispatching method."""
    return a is b or a == b


@are_equal.register
def _(a: str, b: str) -> bool:
    return a is b or a == b


@are_equal.register
def _(a: ndarray, b: ndarray) -> bool:
    return np.array_equal(a, b)


@are_equal.register
def _(a: collections.abc.Iterable, b) -> bool:
    if not issubclass(type(b), collections.abc.Iterable):
        return False
    return all(are_equal(ai, bi) for ai, bi in itertools.zip_longest(a, b))


@functools.singledispatch
def is_in(where, x) -> bool:
    """Check if 'x' belongs to 'where' dispatcher."""
    if where is None:
        return False
    return x is where or x == where


@is_in.register
def _(where: str, x) -> bool:
    return x is where or x == where


@is_in.register
def _(where: tuple, x) -> bool:
    return any(is_in(i, x) for i in where)


@is_in.register
def _(where: collections.abc.Callable, x) -> bool:
    return where(x)  # type: ignore[no-any-return]


@is_in.register
def _(where: collections.abc.Container, x) -> bool:
    return x in where


def filter_dict(
    a: dict[Any, Any],
    *drop_items,
) -> dict[Any, Any]:
    """Create copy of a dictionary omitting some keys."""
    res = {}
    for k, v in a.items():
        if drop_items and is_in(drop_items, k):
            pass
        elif isinstance(v, dict):
            res[k] = filter_dict(v, *drop_items)
        elif issubclass(type(v), collections.abc.Collection):
            res[k] = deepcopy(v)
        else:
            res[k] = v
    return res


@functools.singledispatch
def make_hashable(x):
    """Create hashable object from 'x'."""
    raise TypeError(f"Don't know how to make {type(x).__name__} objects hashable")


@make_hashable.register
def _(x: collections.abc.Hashable):
    return x


@make_hashable.register
def _(x: str):
    return x


@make_hashable.register
def _(x: collections.abc.Mapping) -> tuple:
    return tuple((k, make_hashable(v)) for k, v in x.items())


@make_hashable.register
def _(x: collections.abc.Iterable) -> tuple:
    return tuple(map(make_hashable, x))


def compute_hash(*items) -> int:
    """Compute hash for a sequence of potentially formally not hashable objects.

    Note:
        Take care on the objects values are stable, while the hashes are in use.
    """
    if len(items) > 1:
        return compute_hash(tuple(map(compute_hash, items)))
    return hash(make_hashable(items[0]))


def is_sorted(a: np.ndarray) -> bool:
    """Check if an array is sorted."""
    return cast(bool, np.all(np.diff(a) > 0))


def mids(a: np.ndarray) -> np.ndarray:
    """Get centers of bins presented with array 'a'."""
    result: ndarray = 0.5 * (a[1:] + a[:-1])
    return result


def prettify_float(x: float, fmt: str = "{:.13g}") -> str:
    """Format float in uniform way."""
    if x.is_integer():
        return str(int(x))
    return fmt.format(x)
