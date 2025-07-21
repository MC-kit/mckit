from __future__ import annotations

import re

import pytest

from mckit import __version__

VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+.*")


def test_version():
    assert VERSION_PATTERN.match(__version__)
    assert __version__ != "0.0.0", "meta information is not correct"


if __name__ == "__main__":
    pytest.main()
