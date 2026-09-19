"""Text utilities."""

from __future__ import annotations

import re

from collections.abc import Callable


def match_comment(comment: list[str], predicate: str | re.Pattern | Callable[[str], bool]) -> bool:
    """Check if this cell trailing comment matches `predicate`.

    Parameters
    ----------
    comment
        lines where to search
    predicate
        what to search for in the comments (string, pattern or callable)

    Returns
    -------
    Does predicate match one of the  comment lines?
    """
    if isinstance(predicate, str):
        return any(predicate in line for line in comment)
    if isinstance(predicate, re.Pattern):
        return any(predicate.search(line) for line in comment)
    if isinstance(predicate, Callable):
        return any(predicate(line) for line in comment)
    msg = f"Predicate of unknown type: {predicate}"
    raise ValueError(msg)


__all__ = ["match_comment"]
