from __future__ import annotations

from pathlib import Path

import pytest

from mckit.cli.runner import mckit
from mckit.parser import from_file
from mckit.utils._resource import path_resolver

data_path_resolver = path_resolver("tests.cli")


def data_filename_resolver(x):
    return str(data_path_resolver(x))


def test_when_there_is_no_args(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(mckit, args=["transform"], catch_exceptions=False)
        assert result.exit_code != 0, "Should fail when no arguments provided"
        assert "Usage:" in result.output


def test_transformation_is_not_defined(runner):
    result = runner.invoke(
        mckit,
        args=["transform", data_filename_resolver("data/simple_cubes.mcnp")],
        catch_exceptions=False,
    )
    assert result.exit_code > 0
    assert "Missing option" in result.output


def test_output_is_not_defined(runner):
    result = runner.invoke(
        mckit,
        args=[
            "transform",
            "--transformation",
            "1",
            data_filename_resolver("data/simple_cubes.mcnp"),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code > 0
    assert "Missing option" in result.output
    assert "output" in result.output


def test_not_existing_mcnp_file(runner):
    result = runner.invoke(
        mckit,
        args=["transform", "-t", "1", "not-existing.mcnp"],
        catch_exceptions=False,
    )
    assert result.exit_code > 0
    assert "Path 'not-existing.mcnp' does not exist" in result.output


@pytest.mark.parametrize(
    "msg, _source, transformation,, expected",
    [
        (
            "identical transformation",
            "data/simple_cubes_with_tallies.mcnp",
            "1",
            "data/simple_cubes_with_tallies.mcnp",
        ),
    ],
)
def test_happy_path(runner, msg, _source, transformation, expected):
    source = data_filename_resolver(_source)
    out = Path(source).name
    transformations = data_filename_resolver("data/brick-transformations.txt")
    with runner.isolated_filesystem():
        result = runner.invoke(
            mckit,
            args=[
                "transform",
                "-t",
                transformation,
                "-i",
                transformations,
                "-o",
                str(out),
                source,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, "Should success"
        out_path = Path(out)
        assert out_path.exists()


@pytest.mark.parametrize(
    "source, transformation, transformations, expected",
    [
        (
            "data/brick1.mcnp",
            "1",
            "data/brick-transformations.txt",
            "data/brick1-x+10.mcnp",
        ),
        (
            "data/brick1.mcnp",
            "2",
            "data/brick-transformations.txt",
            "data/brick1-rot-z90.mcnp",
        ),
    ],
)
def test_when_transform_happy_path(runner, source, transformation, transformations, expected):
    source = data_filename_resolver(source)
    transformations = data_filename_resolver(transformations)
    with runner.isolated_filesystem():
        out = "test_when_transformation_is_specified_by_spec.out"
        result = runner.invoke(
            mckit,
            args=[
                "transform",
                "-o",
                out,
                "-t",
                transformation,
                "-i",
                transformations,
                source,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Failed to transform {source}"
        expected_universe = from_file(data_filename_resolver(expected)).universe
        expected_surfaces = list(expected_universe[0])
        actual_universe = from_file(out).universe
        actual_surfaces = list(actual_universe[0])

        def key(a):
            return a.args[0].options["name"]

        assert sorted(actual_surfaces, key=key) == sorted(expected_surfaces, key=key)


# @pytest.mark.parametrize(
#     "source, expected",
#     [
#         (
#             "cli/data/simple_cubes.mcnp",
#             "title.txt \
#         cells_start.txt cells.txt cells_end.txt \
#         surfaces_start.txt surfaces.txt surfaces_end.txt \
#         materials_start.txt materials.txt materials_end.txt \
#         transformations_start.txt transformations_end.txt \
#         cards.txt \
#         new_line.txt",
#         )
#     ],
# )
# def test_when_separator_files_are_required(runner, source, expected):
#     source = data_filename_resolver(source)
#     with runner.isolated_filesystem():
#         result = runner.invoke(
#             mckit, args=["split", "--separators", source], catch_exceptions=False
#         )
#         assert result.exit_code == 0, "Should success"
#         out = get_default_output_directory(source, ".split")
#         assert out.is_dir()
#         expected = expected.split()
#         for e in expected:
#             assert (out / e).exists()
#         text = (out / "cells_start.txt").read_text(encoding=MCNP_ENCODING)
#         assert is_comment_text(text), "Should be MCNP comment text"


# @pytest.mark.parametrize("source,expected", [
#     ("cli/data/simple_cubes.mcnp", "envelopes.i u1.i u2.i".split()),
# ])
# def test_when_only_source_is_specified(runner, source, expected):
#     source: Path = data_filename_resolver(source)
#     with runner.isolated_filesystem():
#         result = runner.invoke(mckit, args=['split', source], catch_exceptions=False)
#         assert result.exit_code == 0, \
#             "Should success without specified output: " + result.output
#         output: Path = get_default_output_directory(source)
#         for f in expected:
#             p = output / f
#             assert p.exists(), \
#                 f"Should store the file {p} in the default directory '{output}'"
#             model = mk.read_mcnp(p)
#             for cell in model:
#                 assert 'U' not in cell.options or cell.options['U'].name() == 0
#
#
# @pytest.mark.parametrize("source,output,expected", [
#     ("cli/data/simple_cubes.mcnp", "split-1", "envelopes.i u1.i u2.i".split()),
# ])
# def test_when_output_is_specified(runner, source, output, expected):
#     source = data_filename_resolver(source)
#     with runner.isolated_filesystem():
#         output = Path(output)
#         assert not output.exists(), f"The {output} directory should not exist before the test run"
#         result = runner.invoke(mckit, args=['split', "--output", str(output), source], catch_exceptions=False)
#         assert result.exit_code == 0
#         assert output.exists(), f"The {output} directory should exist after the test run"
#         for f in expected:
#             assert (output / f).exists(), \
#                 f"Should store the file {f} in the default directory 'universes'"
#
#
# def test_when_output_file_exists_and_override_is_not_specified(runner):
#     source = data_filename_resolver("cli/data/simple_cubes.mcnp")
#     with runner.isolated_filesystem() as prefix:
#         output = Path(prefix) / "universes/envelopes.i"
#         output.parent.mkdir(parents=True)
#         output.touch(exist_ok=False)
#         result = runner.invoke(
#             mckit,
#             args=["split", source],
#             catch_exceptions=False
#         )
#         assert result.exit_code != 0, \
#             "Should fail when output file exists and --override is not specified"
#
#
# def test_when_output_file_exists_and_override_is_specified(runner):
#     source = data_filename_resolver("cli/data/simple_cubes.mcnp")
#     with runner.isolated_filesystem() as prefix:
#         output = Path(prefix) / "simple_cubes./envelopes.i"
#         output.parent.mkdir(parents=True)
#         output.touch(exist_ok=False)
#         result = runner.invoke(
#             mckit,
#             args=["--override", "split", source],
#             catch_exceptions=False
#         )
#         assert result.exit_code == 0, \
#             "Should success when output file exists and --override is specified"
#
#
#
# def test_fill_descriptor(runner):
#     source = data_filename_resolver("cli/data/simple_cubes.mcnp")
#     with runner.isolated_filesystem() as prefix:
#         output = Path(prefix) / "universes/fill-descriptor.toml"
#         result = runner.invoke(
#             mckit,
#             args=["split", source],
#             catch_exceptions=False
#         )
#         assert result.exit_code == 0, "Should success"
#         assert output.exists()
#         with output.open() as fid:
#             fill_descriptor = fid.read()
#             assert fill_descriptor.find('simple_cubes.mcnp')
#             fill_descriptor = tk.parse(fill_descriptor)
#             assert 'created' in fill_descriptor
#             assert '2' in fill_descriptor
#             assert 'universe' in fill_descriptor['2']
#             assert 1 == fill_descriptor['2']['universe']
#             assert 'u1.i' == fill_descriptor['2']['file']
#
#
#
# def test_fill_descriptor_when_fill_descriptor_file_is_specified(runner):
#     source = data_filename_resolver("cli/data/simple_cubes.mcnp")
#     with runner.isolated_filesystem() as prefix:
#         fill_descriptor_path = Path(prefix) / "fill-descriptor-special.toml"
#         result = runner.invoke(
#             mckit,
#             args=["split", "--fill-descriptor", str(fill_descriptor_path), source],
#             catch_exceptions=False
#         )
#         assert result.exit_code == 0, "Should success"
#         assert fill_descriptor_path.exists()
#
#
# def test_anonymous_transformation(runner):
#     source = data_filename_resolver("cli/data/cubes_with_fill_transforms.mcnp")
#     with runner.isolated_filesystem() as prefix:
#         output = Path(prefix) / "cubes_with_fill_transforms.universes"
#         result = runner.invoke(
#             mckit,
#             args=["split", source],
#             catch_exceptions=False
#         )
#         assert result.exit_code == 0, "Should success"
#         with open(output / "fill-descriptor.toml") as fid:
#             descriptor = tk.parse(fid.read())
#             spec = descriptor['2']['transform']
#             assert float(spec[1]) == -1.0, "Fill descriptor is wrong"
