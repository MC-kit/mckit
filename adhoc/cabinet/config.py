#!python
"""TODO..."""
from __future__ import annotations

from typing import Literal

from pathlib import Path

# noinspection PyPackageRequirements
from pydantic import Field


def main():
    """TODO..."""
    pass


if __name__ == "__main__":
    main()


def file_field(path: str, status: Literal["exists", "new"] = "exists") -> Field:
    """Setup data field for a file.

    Args:
        path: default value for a field
        status: how to check the file

    Returns:
        pydantic Field
    """
    return Field(Path(path).expanduser(), validate_default=status != "new")
