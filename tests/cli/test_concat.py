from __future__ import annotations

from pathlib import Path

from mckit.cli.runner import mckit


def test_when_there_is_no_args(runner):
    result = runner.invoke(mckit, args=["concat"], catch_exceptions=False)
    assert result.exit_code != 0, "Should fail when no arguments provided"
    assert "Usage:" in result.output


def test_not_existing_file(runner):
    result = runner.invoke(mckit, args=["concat", "not-existing.txt"], catch_exceptions=False)
    assert result.exit_code > 0
    assert "Path 'not-existing.txt' does not exist" in result.output


def test_when_only_part_is_specified(runner, data):
    part = data / "cli/concat/test_load_table_1.csv"
    result = runner.invoke(mckit, args=["concat", str(part)], catch_exceptions=False)
    assert result.exit_code == 0, "Should success without specified output: " + result.output
    assert "x   y" in result.output, (
        "Should send output to stdout, when the output is not specified"
    )


def test_when_output_is_specified(runner, data):
    part = data / "cli/concat/test_load_table_1.csv"
    output_file = Path.cwd() / "test_when_output_is_specified.txt"
    result = runner.invoke(
        mckit,
        args=["concat", "--output", str(output_file), str(part)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, "Should success with specified output: " + result.output
    assert output_file.exists(), f"Should create output file {output_file!r}"
    # noinspection PyCompatibility
    assert "x   y" in output_file.read_text(encoding="Cp1251"), (
        f"Should contain content of {part!r}"
    )


# noinspection PyCompatibility
def test_when_two_parts_are_specified(runner, data):
    part1 = data / "cli/concat/test_load_table_1.csv"
    part2 = data / "cli/concat/test_load_table_2.csv"
    output_file = Path.cwd() / "test_when_output_is_specified.txt"
    result = runner.invoke(
        mckit,
        args=["concat", "--output", str(output_file), str(part1), str(part2)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, "Should success with specified output: " + result.output
    assert output_file.exists(), f"Should create output file {output_file!r}"
    text = output_file.read_text(encoding="Cp1251")
    assert "x   y" in text, f"Should contain content of {part1!r}"
    assert "x    ;   y" in text, f"Should contain content of {part2!r}"


def test_when_output_file_exists_and_override_is_not_specified(runner, data):
    part = data / "cli/concat/test_load_table_1.csv"
    output_file = Path.cwd() / "test_when_output_is_specified.txt"
    output_file.touch(exist_ok=False)
    result = runner.invoke(
        mckit, args=["concat", "-o", str(output_file), str(part)], catch_exceptions=False
    )
    assert result.exit_code != 0, "Should fail when output file exist and override is not specified"
