"""Build mckit.

The `build` method from this module is called by poetry build system
to set up proper options for actual builder.

The module builds and arrange C-dependency ``nlopt`` before own build.
"""

from __future__ import annotations

from typing import Any

import shutil
import sys
import sysconfig

from distutils import log as distutils_log
from pathlib import Path
from pprint import pprint

import skbuild
import skbuild.constants

__all__ = ["build"]

WIN = sys.platform.startswith("win32") and "mingw" not in sysconfig.get_platform()
MACOS = sys.platform.startswith("darwin")
DEBUG = True

if WIN:
    suffixes = ("pyd", "dll")
elif MACOS:
    suffixes = ("dylib",)
else:
    suffixes = ("so",)


def build(setup_kwargs: dict[str, Any]) -> None:
    """Build C-extensions."""
    distutils_log.info("*** Running skbuild.setup")
    skbuild.setup(**setup_kwargs, script_args=["build_ext"])

    pkg = setup_kwargs["name"]
    distutils_log.info(f"Load extensions and their dependencies to {pkg}")
    install_dir = Path(skbuild.constants.CMAKE_INSTALL_DIR())
    src_dirs = (install_dir / x for x in (f"src/{pkg}", "bin"))
    dest_dir = Path(f"src/{pkg}")

    # Delete C-extensions copied in previous runs, just in case.
    for suffix in ("so", "dylib", "pyd", "dll"):
        remove_files(dest_dir, f"**/*.{suffix}")
    for src_dir in src_dirs:
        distutils_log.info(f"*** Copying libraries {src_dir} -> {dest_dir}")
        for suffix in ("so", "dylib", "pyd", "dll"):
            # Copy built C-extensions and dependent libs back to the project.
            copy_files(src_dir, dest_dir, f"**/*.{suffix}")

    if DEBUG:
        save_setup_kwargs(setup_kwargs)


def remove_files(target_dir: Path, pattern: str) -> None:
    """Delete files matched with a glob pattern in a directory tree."""
    for path in target_dir.glob(pattern):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        distutils_log.info(f"removed {path}")


def copy_files(src_dir: Path, dest_dir: Path, pattern: str) -> None:
    """Copy files matched with a glob pattern in a directory tree to another."""
    for src in src_dir.glob(pattern):
        dest = dest_dir / src.relative_to(src_dir)
        if src.is_dir():
            # NOTE: inefficient if subdirectories also match to the pattern.
            copy_files(src, dest, "*")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            distutils_log.info(f"copied {src} to {dest}")


def save_setup_kwargs(setup_kwargs: dict[str, Any]) -> None:
    """Save resulting setup_kwargs for examining."""
    kwargs_path = Path(__file__).parent / "poetry_setup_kwargs.txt"
    with kwargs_path.open(mode="w") as fid:
        pprint(setup_kwargs, fid, indent=4)
