from __future__ import annotations

import pytest

from mckit.cli.runner import mckit


def test_when_there_is_no_args(runner):
    result = runner.invoke(mckit, args=["check"], catch_exceptions=False)
    assert result.exit_code != 0, "Should fail when no arguments provided"
    assert "Usage:" in result.output


def test_not_existing_mcnp_file(runner):
    result = runner.invoke(mckit, args=["check", "not-existing.mcnp"], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Path 'not-existing.mcnp' does not exist" in result.output


@pytest.mark.parametrize(
    "source, expected",
    [("cli//simple_cubes.mcnp", "cells;surfaces;transformations;compositions")],
)
def test_good_path(runner, source, expected, data):
    source = data / source
    result = runner.invoke(mckit, args=["--quiet", "check", str(source)], catch_exceptions=False)
    assert result.exit_code == 0, "Should success"
    for e in expected.split(";"):
        assert e in result.output
