from __future__ import annotations

import pytest

from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()
