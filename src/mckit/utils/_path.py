from __future__ import annotations

from collections.abc import Callable
from pathlib import Path


def search_path_upward(
    predicate: Callable[[Path], bool], *, start: Path | None = None
) -> Path | None:
    """Search path matching `preidicate` up from `start` path.

    Parameters
    ----------
    predicate
        to check condition on path
    start, optional
        starting dir, default current work dir

    Returns
    -------
        path to the found directory, if any, None otherwise
    """
    if start is None:
        start = Path.cwd()
    path = start
    while True:
        if predicate(path):
            return path
        if path.parent == path:
            return None
        path = path.parent


def has_subdir(subdirectory: str) -> Callable[[Path], bool]:
    """Create predicate to check if a path has given `subdirectory`.

    Parameters
    ----------
    subdirectory
        to search for

    Returns
    -------
        Callable predicate
    """

    def _call(path: Path) -> bool:
        return (path / subdirectory).is_dir()

    return _call


def find_git_root_dir() -> Path | None:
    """Find root directory of a git repository.

    Returns
    -------
        the directory having ".git" subdirectory
    """
    return search_path_upward(has_subdir(".git"))
