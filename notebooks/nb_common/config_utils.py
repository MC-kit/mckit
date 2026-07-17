from __future__ import annotations

from typing import Final, Iterable

import os

from pathlib import Path

HOST: Final[str] = os.uname().nodename

def find_git_root(start_from: Path = Path.cwd()) -> Path:
    for p in scan_dirs_up(start_from):
        if (p / ".git").exists():
            return p.absolute()
    msg = f"Cannot find git repository root from {start_from=}"
    raise ValueError(msg)


def scan_dirs_up(start_from: Path) -> Iterable[Path]:
    check_dir(start_from)
    while start_from != start_from.parent:
        yield start_from
        start_from = start_from.parent


def mkpath(path: str | Path) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    return path


def check_file(path: str | Path) -> Path:
    path = mkpath(path)
    if not path.is_file():
        msg = f"Not a file: {path}"
        raise ValueError(msg)
    return path


def check_files(*files: str | Path) -> Iterable[Path]:
    for path in files:
        yield check_file(path)


def check_dir(path: str | Path) -> Path:
    path = mkpath(path)
    if not path.is_dir():
        msg = f"Not a dir: {path}"
        raise ValueError(msg)
    return path


def check_dirs(*dirs: Path) -> Iterable[Path]:
    for path in dirs:
        yield check_dir(path)


def mk_dirs(*dirs: str | Path) -> Iterable[Path]:
    for path in dirs:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        yield path


def setup_dirs(root_dir: Path, *subdirectories: str) -> Iterable[Path]:
    """Setup directories for input data

    Join given subdirectories to the root_dir annotations
    check if the directories exist.

    Parameters
    ----------
    root_dir
        base for the following subdirectories.
    subdirectories
        what to join

    Yields
    ------
    Joined path to subdirectories
    """
    yield from (root_dir / sub for sub in subdirectories)
