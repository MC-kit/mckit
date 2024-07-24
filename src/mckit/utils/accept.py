"""The interfaces to facilitate adding new functionality to an hierarchy of classes (Visitor pattern)."""

from __future__ import annotations

from typing import Any, NoReturn

from collections.abc import Callable
from contextlib import AbstractContextManager
from functools import reduce

TVisitor = Callable[..., AbstractContextManager]


def accept(acceptor: Any, visitor: TVisitor, *args, **kwargs) -> Any:
    with visitor(acceptor, *args, **kwargs) as recurse:
        items_visitor, initial = recurse
        return reduce(items_visitor, acceptor, initial)


def on_unknown_acceptor(acceptor: Any) -> NoReturn:
    raise NotImplementedError(f"Not implemented for {type(acceptor).__name__}")
