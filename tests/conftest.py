from __future__ import annotations

from pathlib import Path

# noinspection PyPackageRequirements
import pytest

HERE = Path(__file__).parent
DATA = (HERE / "data").absolute()


@pytest.fixture(scope="session")
def data() -> Path:
    """Get Path to tests/data directory.

    Returns
    -------
    Path to tests/data directory
    """
    return DATA


@pytest.fixture
def cd_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporarily switch to temp directory.

    Returns
    -------
    Path: current (temporal) directory
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
