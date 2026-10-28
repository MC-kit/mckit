from __future__ import annotations

from itertools import repeat
from pathlib import Path

import pytest

from mckit.utils import (
    check_if_all_paths_exist,
    check_if_path_exists,
    find_git_root_dir,
    get_last_line,
    make_dirs,
    search_path_upward,
)


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


def test_get_last_line(cd_tmpdir):
    test_path = Path("test_get_last_line.txt")
    test_path.touch()
    actual = get_last_line(test_path)
    assert actual == "", "Empty file -> empty line"
    test_path.write_bytes(b"\n")
    actual = get_last_line(test_path)
    assert actual == "\n", "Single empty line -> empty line with \\n"
    line = "xyz " * 10
    test_path.write_text(line)
    actual = get_last_line(test_path)
    assert actual == line, "One line -> the line itself"

    def _make_text(line, n):
        return "\n".join(repeat(line, n))

    test_path.write_text(_make_text(line, 2))
    actual = get_last_line(test_path)
    assert actual == line, "Two lines -> the last line"
    actual = get_last_line(test_path, chunk_size=2)
    assert actual == line, "Two lines, small chunk -> the last line"

    def _make_text_with_nl(line, n):
        return _make_text(line, n) + "\n"

    line_with_nl = line + "\n"
    test_path.write_text(_make_text_with_nl(line, 2))
    actual = get_last_line(test_path)
    assert actual == line_with_nl, "Two lines -> the last line"
    actual = get_last_line(test_path, chunk_size=2)
    assert actual == line_with_nl, "Two lines, small chunk -> the last line"
