from __future__ import annotations

import sys

from pathlib import Path

import numpy as np
import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from numpy.testing import assert_array_equal

from mckit.cli.commands.decompose import get_default_output_directory
from mckit.cli.runner import mckit
from mckit.parser import from_file
from mckit.utils.resource import path_resolver

data_path_resolver = path_resolver("tests")


def data_filename_resolver(x):
    return str(data_path_resolver(x))


@pytest.mark.parametrize(
    "path, expected_cells",
    [
        ("cli/data/simple_cubes.mcnp", 3),
        ("cli/data/simple_cubes.universes/envelopes.i", 3),
        ("cli/data/simple_cubes.universes/u1.i", 2),
        ("cli/data/simple_cubes.universes/u2.i", 2),
    ],
)
def test_input_files_reading(path, expected_cells):
    universe = from_file(data_filename_resolver(path)).universe
    assert len(universe) == expected_cells, f"Failed to read from file {path}"


def test_help_decompose(runner):
    result = runner.invoke(mckit, args=["decompose", "--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: mckit decompose" in result.output


def test_when_there_is_no_args(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(mckit, args=["decompose"], catch_exceptions=False)
        assert result.exit_code != 0, "Should fail when no arguments provided"
        assert "Usage:" in result.output


def test_not_existing_mcnp_file(runner):
    result = runner.invoke(mckit, args=["decompose", "not-existing.imcnp"], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Path 'not-existing.imcnp' does not exist" in result.output


@pytest.mark.parametrize("source, expected", [("parser_test_data/parser1.txt", "envelopes.i")])
def test_when_there_are_no_universes(runner, source, expected):
    source = data_filename_resolver(source)
    with runner.isolated_filesystem():
        result = runner.invoke(
            mckit, args=["decompose", "-o", "universes", source], catch_exceptions=False
        )
        assert result.exit_code == 0, "Should success without universes"
        assert Path("universes/envelopes.i").exists(), (
            "Should store the only envelopes.i file in the default directory 'universes'"
        )


@pytest.mark.parametrize(
    "source,expected", [("cli/data/simple_cubes.mcnp", ["envelopes.i", "u1.i", "u2.i"])]
)
def test_when_only_source_is_specified(runner, source, expected):
    source: str = data_filename_resolver(source)
    with runner.isolated_filesystem():
        run_result = runner.invoke(mckit, args=["decompose", source], catch_exceptions=False)
        assert run_result.exit_code == 0, (
            "Should success without specified output: " + run_result.output
        )
        output: Path = get_default_output_directory(source)
        for f in expected:
            p = output / f
            assert p.exists(), f"Should store the file {p} in the default directory {output!r}"
            model = from_file(p).universe
            for cell in model:
                assert "U" not in cell.options or cell.options["U"].name() == 0


@pytest.mark.parametrize(
    "source,output,expected",
    [("cli/data/simple_cubes.mcnp", "split-1", ["envelopes.i", "u1.i", "u2.i"])],
)
def test_when_output_is_specified(runner, source, output, expected):
    source = data_filename_resolver(source)
    with runner.isolated_filesystem():
        output = Path(output)
        assert not output.exists(), f"The {output} directory should not exist before the test run"
        result = runner.invoke(
            mckit,
            args=["decompose", "--output", str(output), source],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert output.exists(), f"The {output} directory should exist after the test run"
        for f in expected:
            assert (output / f).exists(), (
                f"Should store the file {f} in the default directory 'universes'"
            )


def test_when_output_file_exists_and_override_is_not_specified(runner):
    source = data_filename_resolver("cli/data/simple_cubes.mcnp")
    with runner.isolated_filesystem() as prefix:
        output = Path(prefix) / "simple_cubes.universes/envelopes.i"
        output.parent.mkdir(parents=True)
        output.touch(exist_ok=False)
        result = runner.invoke(mckit, args=["decompose", source], catch_exceptions=False)
        assert result.exit_code != 0, (
            "Should fail when output file exists and --override is not specified"
        )


def test_when_output_file_exists_and_override_is_specified(runner):
    source = data_filename_resolver("cli/data/simple_cubes.mcnp")
    with runner.isolated_filesystem() as prefix:
        output = Path(prefix) / "simple_cubes./envelopes.i"
        output.parent.mkdir(parents=True)
        output.touch(exist_ok=False)
        result = runner.invoke(
            mckit, args=["--override", "decompose", source], catch_exceptions=False
        )
        assert result.exit_code == 0, (
            "Should success when output file exists and --override is specified"
        )


def test_fill_descriptor(runner):
    source = data_filename_resolver("cli/data/simple_cubes.mcnp")
    with runner.isolated_filesystem() as prefix:
        output = Path(prefix) / "simple_cubes.universes/fill-descriptor.toml"
        result = runner.invoke(mckit, args=["decompose", source], catch_exceptions=False)
        assert result.exit_code == 0, "Should success"
        assert output.exists()
        with output.open() as fid:
            fill_descriptor = fid.read()
            assert fill_descriptor.find("simple_cubes.mcnp")
            fill_descriptor = tomllib.loads(fill_descriptor)
            assert "created" in fill_descriptor
            assert "2" in fill_descriptor
            assert "universe" in fill_descriptor["2"]
            assert fill_descriptor["2"]["universe"] == 1
            assert fill_descriptor["2"]["file"] == "u1.i"


def test_fill_descriptor_when_fill_descriptor_file_is_specified(runner):
    source = data_filename_resolver("cli/data/simple_cubes.mcnp")
    with runner.isolated_filesystem() as prefix:
        fill_descriptor_path = Path(prefix) / "fill-descriptor-special.toml"
        result = runner.invoke(
            mckit,
            args=["decompose", "--fill-descriptor", str(fill_descriptor_path), source],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, "Should success"
        assert fill_descriptor_path.exists()


def test_anonymous_transformation(runner):
    source = data_filename_resolver("cli/data/cubes_with_fill_transforms.mcnp")
    with runner.isolated_filesystem() as prefix:
        output = Path(prefix) / "cubes_with_fill_transforms.universes"
        result = runner.invoke(mckit, args=["decompose", source], catch_exceptions=False)
        assert result.exit_code == 0, "Should success"
        with (output / "fill-descriptor.toml").open("rb") as fid:
            descriptor = tomllib.load(fid)
            spec = descriptor["2"]["transform"]
            assert len(spec) == 3
            spec1 = np.fromiter(map(float, spec), dtype=float)
            assert_array_equal(spec1, [0.0, -1.0, 0.0], f"Fill descriptor {spec1} is wrong")


def test_named_transformation(runner):
    source = data_filename_resolver("cli/data/cubes_with_fill_named_transforms.mcnp")
    with runner.isolated_filesystem() as prefix:
        output = Path(prefix) / "cubes_with_fill_named_transforms.universes"
        result = runner.invoke(mckit, args=["decompose", source], catch_exceptions=False)
        assert result.exit_code == 0, "Should success"
        with (output / "fill-descriptor.toml").open("rb") as fid:
            descriptor = tomllib.load(fid)
            spec = descriptor["2"]["transform"]
            assert spec == 1, f"Fill descriptor {spec} is wrong"
            transforms = descriptor["named_transformations"]
            assert "tr1" in transforms, "Should store transformation tr1"
            transform = transforms["tr1"]
            transform_params = np.fromiter(map(float, transform), dtype=float)
            assert transform_params.size == 3, "Only translation is specified for tr1"
            (
                assert_array_equal(transform_params, [0, -1.0, 0]),
                f"Invalid transform {transform_params}",
            )
            assert transforms is not None
