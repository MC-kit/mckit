from __future__ import annotations

from mckit.utils import find_git_root_dir, search_path_upward


def test_find_git_root():
    actual = find_git_root_dir()
    assert actual is not None, "Shoud find git root"
    assert actual.parts[-1] == "mckit", "The repository name is 'mckit'"


def test_search_path_upward_fail():
    actual = search_path_upward(lambda _: False)
    assert actual is None, "Should not find anything"
