from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

MCNP_ENCODING = "Cp1251"
"""The encoding used in SuperMC when creating MCNP models code.

Some symbols are not Unicode.
"""


def make_dir(d: Path) -> Path:
    """Create directory."""
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_dirs(*dirs: Path) -> Generator[Path]:
    yield from (make_dir(f) for f in dirs)


def check_if_path_exists(p: Path) -> Path:
    if p.exists():
        return p
    raise FileNotFoundError(f'Path "{p}" does not exist')


def check_if_all_paths_exist(*paths: Path) -> Generator[Path]:
    yield from map(check_if_path_exists, paths)
