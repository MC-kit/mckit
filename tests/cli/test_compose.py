from __future__ import annotations

from pathlib import Path

import pytest

from mckit.cli.runner import mckit
from mckit.parser import from_file
from mckit.universe import collect_transformations
from mckit.utils._resource import path_resolver

data_path_resolver = path_resolver("tests.cli")


def data_filename_resolver(x):
    return str(data_path_resolver(x))


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


def test_when_output_is_not_specified(runner):
    source = data_filename_resolver("data/simple_cubes.mcnp")
    result = runner.invoke(mckit, args=["compose", str(source)], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Missing option '--output'" in result.output


@pytest.mark.parametrize(
    "source, output, expected",
    [
        (
            "data/simple_cubes.universes/envelopes.i",
            "simple_cubes_restored.i",
            "data/simple_cubes.mcnp",
        )
    ],
)
def test_when_fill_descriptor_is_not_specified(runner, source, output, expected):
    source = data_filename_resolver(source)
    with runner.isolated_filesystem() as test_folder:
        result = runner.invoke(
            mckit, args=["compose", "--output", output, source], catch_exceptions=False
        )
        assert result.exit_code == 0, (
            "Should success using fill_descriptor in the same directory as source file"
        )
        assert Path(output).exists(), f"Should create file {output} file in {test_folder}"
        actual = from_file(output)
        expected = from_file(data_filename_resolver(expected))
        assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"


@pytest.mark.parametrize(
    "source, output, expected",
    [
        (
            "data/cubes_with_fill_transforms.universes/envelopes.i",
            "cubes_with_fill_transforms.i",
            "data/cubes_with_fill_transforms.mcnp",
        )
    ],
)
def test_anonymous_transforms(runner, source, output, expected):
    source = data_filename_resolver(source)
    with runner.isolated_filesystem() as test_folder:
        result = runner.invoke(
            mckit, args=["compose", "--output", output, source], catch_exceptions=False
        )
        assert result.exit_code == 0, (
            "Should success using fill_descriptor in the same directory as source file"
        )
        assert Path(output).exists(), f"Should create file {output} file in {test_folder}"
        actual = from_file(output)
        expected = from_file(data_filename_resolver(expected))
        assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"


@pytest.mark.parametrize(
    "universes",
    [
        "cubes_with_fill_named_transforms",
        "two_cubes_with_the_same_filler",
        "shared_surface",
    ],
)
def test_compose(runner, universes):
    source = f"data/{universes}.universes/envelopes.i"
    output = f"{universes}.i"
    expected = f"data/{universes}.mcnp"
    source = data_filename_resolver(source)
    assert Path(source).exists(), f"File {source} does not exist"
    with runner.isolated_filesystem() as test_folder:
        result = runner.invoke(
            mckit, args=["compose", "--output", output, source], catch_exceptions=False
        )
        assert result.exit_code == 0, (
            "Should success using fill_descriptor in the same directory as source file"
        )
        assert Path(output).exists(), f"Should create file {output} file in {test_folder}"
        actual = from_file(output)
        expected = from_file(data_filename_resolver(expected))
        assert actual.universe.has_equivalent_cells(expected.universe), "Cells differ"
        actual_transformations = collect_transformations(actual.universe)
        expected_transformations = collect_transformations(expected.universe)
        assert actual_transformations == expected_transformations, (
            "The transformations should be the same"
        )
