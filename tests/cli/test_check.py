from __future__ import annotations

import pytest

from mckit.cli.runner import mckit
from mckit.utils._resource import path_resolver

data_path_resolver = path_resolver("tests")


def data_filename_resolver(x):
    return str(data_path_resolver(x))


def test_when_there_is_no_args(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(mckit, args=["check"], catch_exceptions=False)
        assert result.exit_code != 0, "Should fail when no arguments provided"
        assert "Usage:" in result.output


def test_not_existing_mcnp_file(runner):
    result = runner.invoke(mckit, args=["check", "not-existing.mcnp"], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Path 'not-existing.mcnp' does not exist" in result.output


@pytest.mark.parametrize(
    "source, expected",
    [("cli/data/simple_cubes.mcnp", "cells;surfaces;transformations;compositions")],
)
def test_good_path(runner, source, expected):
    source = data_filename_resolver(source)
    result = runner.invoke(mckit, args=["--quiet", "check", source], catch_exceptions=False)
    assert result.exit_code == 0, "Should success"
    for e in expected.split(";"):
        assert e in result.output
