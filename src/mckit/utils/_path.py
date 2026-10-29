from __future__ import annotations

import os

from collections.abc import Callable, Generator
from os import PathLike
from pathlib import Path


def scan_dirs_up(start_from: Path) -> Generator[Path]:
    while start_from != start_from.parent:
        yield start_from
        start_from = start_from.parent


def search_path_upward(
    predicate: Callable[[Path], bool], *, start: Path | None = None
) -> Path | None:
    """Search path matching `predicate` up from `start` path.

    Parameters
    ----------
    predicate
        to check condition on path
    start
        starting dir, default current work dir

    Returns
    -------
        path to the found directory, if any, None otherwise
    """
    if start is None:
        start = Path.cwd()
    for path in scan_dirs_up(start):
        if predicate(path):
            return path
    return None


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


def mkpath(path: str | Path) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    return path


def check_file(path: str | Path, *, follow_symlinks: bool = True) -> Path:
    path = mkpath(path)
    if not path.is_file(follow_symlinks=follow_symlinks):  # ty: ignore[unknown-argument]
        msg = f"Not a file: {path}"
        raise ValueError(msg)
    return path


def check_files(*files: str | Path) -> Generator[Path]:
    return (check_file(path) for path in files)


def make_dir(d: str | Path, *, parents=True, exist_ok=True) -> Path:
    """Create directory.

    Parameters
    ----------
    d
        directory to create
    parents
        allow to create parents
    exist_ok
        ignore, if exists

    Returns
    -------
    Full path to the created directory
    """
    p = mkpath(d)
    p.mkdir(parents=parents, exist_ok=exist_ok)
    return p


mkdir = make_dir


def make_dirs(*dirs: str | Path) -> Generator[Path]:
    """Create dirs, if not exist.

    Parameters
    ----------
    dirs
        directories to create

    Returns
    -------
    Generator of paths to created directories
    """
    return (make_dir(f) for f in dirs)


mkdirs = make_dirs


def check_if_path_exists(p: Path, *, follow_symlinks: bool = True) -> Path:
    if p.exists(follow_symlinks=follow_symlinks):
        return p
    raise FileNotFoundError(f'Path "{p}" does not exist')


def check_if_all_paths_exist(*paths: Path, follow_symlinks: bool = True) -> Generator[Path]:
    return (check_if_path_exists(x, follow_symlinks=follow_symlinks) for x in paths)


def check_dir(path: Path) -> Path:
    if not path.is_dir():
        msg = f"Not a dir: {path}"
        raise ValueError(msg)
    return path


def check_dirs(*dirs: Path) -> Generator[Path]:
    return (check_dir(path) for path in dirs)


def join_dirs(root_dir: Path, *subdirectories: str) -> Generator[Path]:
    """Form names of directories under the given root dir.

    Join given subdirectories to the root_dir annotations
    check if the directories exist.

    Parameters
    ----------
    root_dir
        base for the following subdirectories.
    subdirectories
        what to join

    Returns
    -------
    Generator for Joined path to subdirectories
    """
    return (root_dir / sub for sub in subdirectories)


_16M = 1 << 24


def get_last_line(
    file_path: PathLike, chunk_size: int = 1024, encoding="utf-8", errors="strict"
) -> str:
    r"""Read last line of a file.

    The last line is the text between the last "\n" and end of file or,
    if "\n" is the last character in the file, between the previous "\n"
    and the last one (including it). The "\r" character, if present,
    is removed to mimic text reading.

    Parameters
    ----------
    file_path
        ... to the file to read from
    chunk_size
        where to start to search fro the last line

    Returns
    -------
    str
        the last line from the file
    """
    with Path(file_path).open("rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        if file_size == 0:
            return ""

        position = file_size
        last_line = b""

        while position > 0:
            chunk_size = min(chunk_size, position)
            position -= chunk_size
            f.seek(position)
            chunk = f.read(chunk_size)

            # Check for newline in the chunk
            end = len(chunk)

            if chunk[-1] == 10:
                if last_line:
                    break
                end -= 1

            newline_pos = chunk.rfind(b"\n", 0, end)

            if newline_pos != -1:
                last_line = chunk[newline_pos + 1 :] + last_line
                break

            last_line = chunk + last_line

            if chunk_size < _16M:  # pragma: no cover
                chunk_size *= 2

        # Handle case where file has no newlines or single line
        if not last_line and position == 0:  # pragma: no cover
            f.seek(0)
            last_line = f.read()

    if len(last_line) > 2 and last_line[-1] == 10 and last_line[-2] == 13:
        # mimic text reading
        last_line = last_line[:-2] + b"\n"

    return last_line.decode(encoding=encoding, errors=errors)
