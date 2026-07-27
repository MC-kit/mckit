from __future__ import annotations

from collections.abc import Callable, Generator
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
    if not path.is_file(follow_symlinks=follow_symlinks):
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
