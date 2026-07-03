from __future__ import annotations

from pathlib import Path

import pytest

from mckit.cli.runner import mckit
from mckit.parser import from_file
from mckit.universe import collect_transformations


def test_help_compose(runner):
    result = runner.invoke(mckit, args=["compose", "--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: mckit compose" in result.output


def test_when_there_is_no_args(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(mckit, args=["compose"], catch_exceptions=False)
        assert result.exit_code != 0, "Should fail when no arguments provided"
        assert "Usage:" in result.output


def test_not_existing_envelopes_file(runner):
    result = runner.invoke(mckit, args=["compose", "not-existing.mcnp"], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Path 'not-existing.mcnp' does not exist" in result.output


def test_when_output_is_not_specified(runner, data):
    source = data / "cli/simple_cubes.mcnp"
    result = runner.invoke(mckit, args=["compose", str(source)], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Missing option '--output'" in result.output


@pytest.mark.parametrize(
    "source, output, expected",
    [
        (
            "simple_cubes.universes/envelopes.i",
            "simple_cubes_restored.i",
            "simple_cubes.mcnp",
        )
    ],
)
def test_when_fill_descriptor_is_not_specified(runner, source, output, expected, data):
    source = data / "cli" / source
    result = runner.invoke(
        mckit, args=["compose", "--output", output, str(source)], catch_exceptions=False
    )
    assert result.exit_code == 0, (
        "Should success using fill_descriptor in the same directory as source file"
    )
    assert Path(output).exists(), f"Should create file {output} file in {Path.cwd()}"
    actual = from_file(output)
    expected = from_file(data / "cli" / expected)
    assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"


@pytest.mark.parametrize(
    "source, output, expected",
    [
        (
            "cubes_with_fill_transforms.universes/envelopes.i",
            "cubes_with_fill_transforms.i",
            "cubes_with_fill_transforms.mcnp",
        )
    ],
)
def test_anonymous_transforms(runner, source, output, expected, data):
    source = data / "cli" / source
    result = runner.invoke(
        mckit, args=["compose", "--output", output, str(source)], catch_exceptions=False
    )
    assert result.exit_code == 0, (
        "Should success using fill_descriptor in the same directory as source file"
    )
    assert Path(output).exists(), f"Should create file {output} file in {cd_tmpdir}"
    actual = from_file(output)
    expected = from_file(data / "cli" / expected)
    assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"


@pytest.mark.parametrize(
    "universes",
    [
        "cubes_with_fill_named_transforms",
        "two_cubes_with_the_same_filler",
        "shared_surface",
    ],
)
def test_compose(runner, universes, data):
    source = f"{universes}.universes/envelopes.i"
    output = f"{universes}.i"
    expected = f"{universes}.mcnp"
    source = data / "cli" / source
    assert Path(source).exists(), f"File {source} does not exist"
    result = runner.invoke(
        mckit, args=["compose", "--output", output, str(source)], catch_exceptions=False
    )
    assert result.exit_code == 0, (
        "Should success using fill_descriptor in the same directory as source file"
    )
    assert Path(output).exists(), f"Should create file {output} file in {cd_tmpdir}"
    actual = from_file(output)
    expected = from_file(data / "cli" / expected)
    assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"
    actual_transformations = collect_transformations(actual.universe)
    expected_transformations = collect_transformations(expected.universe)
    assert actual_transformations == expected_transformations, (
        "The transformations should be the same"
    )
