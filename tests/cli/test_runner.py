from __future__ import annotations

from io import StringIO

import pytest

from mckit.cli._logging import logger
from mckit.cli.runner import VERSION, mckit, meta


def test_version_command(runner):
    result = runner.invoke(mckit, args=["--version"], catch_exceptions=False)
    assert result.exit_code == 0, "Should success on '--version' option: " + result.output
    assert VERSION in result.output, "print version on 'version' command"


def test_help_command(runner):
    result = runner.invoke(mckit, args=["--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: " in result.output
    assert meta.__summary__ in result.output


def test_fails_on_unknown_command(runner):
    result = runner.invoke(mckit, args=["unknown_command"], catch_exceptions=False)
    assert result.exit_code != 0, "Have somebody implemented 'unknown_command' already?"
    assert "Usage: " in result.output


def test_writes_to_logger_on_errors(runner):
    sink = StringIO()
    logger.add(sink)
    result = runner.invoke(mckit, args=["check", "not_existing.i"], catch_exceptions=False)
    assert result.exit_code != 0, "Does not_existing.i exist?"


if __name__ == "__main__":
    pytest.main()
