from __future__ import annotations

from itertools import repeat
from pathlib import Path

import pytest

from mckit.utils import (
    check_dir,
    check_dirs,
    check_file,
    check_files,
    check_if_all_paths_exist,
    check_if_path_exists,
    find_git_root_dir,
    get_last_line,
    join_dirs,
    make_dirs,
    mkpath,
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


def test_search_path_upward_with_start(tmp_path):
    assert search_path_upward(lambda p: p == tmp_path, start=tmp_path) == tmp_path
    assert search_path_upward(lambda _: False, start=tmp_path) is None


def test_mkpath():
    assert mkpath("abc") == Path("abc")
    p = Path("abc")
    assert mkpath(p) == p


def test_check_file(cd_tmpdir):
    path = Path("a_file.txt")
    path.touch()
    assert check_file(path) == path
    assert check_file(str(path)) == path
    with pytest.raises(ValueError, match="Not a file:"):
        check_file("not-existing.and.never-should-exist")


def test_check_files(cd_tmpdir):
    paths = [Path("a.txt"), Path("b.txt")]
    for p in paths:
        p.touch()
    assert [*check_files(*paths)] == paths
    with pytest.raises(ValueError, match="Not a file:"):
        _ = [*check_files(paths[0], Path("not-existing.and.never-should-exist"))]


def test_check_dir(cd_tmpdir):
    assert check_dir(Path()) == Path()
    with pytest.raises(ValueError, match="Not a dir:"):
        check_dir(Path("not-existing.and.never-should-exist"))


def test_check_dirs(cd_tmpdir):
    dirs = [Path("a"), Path("b")]
    for d in dirs:
        d.mkdir()
    assert [*check_dirs(*dirs)] == dirs
    with pytest.raises(ValueError, match="Not a dir:"):
        _ = [*check_dirs(dirs[0], Path("not-existing.and.never-should-exist"))]


def test_join_dirs(tmp_path):
    actual = [*join_dirs(tmp_path, "a", "b")]
    assert actual == [tmp_path / "a", tmp_path / "b"]


@pytest.mark.parametrize("chunk_size", [1, 1024])
def test_get_last_line_blank_last_line(cd_tmpdir, chunk_size):
    test_path = Path("test_get_last_line_blank.txt")
    test_path.write_bytes(b"a\n\n")
    actual = get_last_line(test_path, chunk_size=chunk_size)
    assert actual == "\n", "Blank last line -> the line with just the newline"
