from __future__ import annotations

from pathlib import Path

import pytest

from mckit.utils._io import check_if_all_paths_exist, check_if_path_exists, make_dirs

TEST_VAR = "TEST_GET_ROOT_DIR_VAR"


def test_mkdirs_and_check_if_all_paths_exist(cd_tmpdir):
    dirs = [*make_dirs(*(Path(f) for f in ["a", "b"]))]
    for p in dirs:
        assert p.exists()
    existing_dirs = [*check_if_all_paths_exist(*dirs)]
    assert existing_dirs == dirs
    with pytest.raises(FileNotFoundError):
        _ = [*check_if_all_paths_exist(Path("not-existing.and.never-should-exist"))]


def test_chk_path(cd_tmpdir):
    check_if_path_exists(Path())
    with pytest.raises(FileNotFoundError):
        check_if_path_exists(Path("not-existing.and.never-should-exist"))
