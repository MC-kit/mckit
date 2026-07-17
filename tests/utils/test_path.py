from __future__ import annotations

from pathlib import Path

import pytest

from mckit.utils import find_git_root_dir, search_path_upward, make_dirs, check_if_all_paths_exist, check_if_path_exists


def test_find_git_root():
    actual = find_git_root_dir()
    assert actual is not None, "Shoud find git root"
    assert actual.parts[-1] == "mckit", "The repository name is 'mckit'"


def test_search_path_upward_fail():
    actual = search_path_upward(lambda _: False)
    assert actual is None, "Should not find anything"


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
