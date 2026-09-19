from __future__ import annotations

import pytest

from click.testing import CliRunner


@pytest.fixture
def runner(cd_tmpdir):
    """Execute click runner in temporary test directory."""
    return CliRunner()
