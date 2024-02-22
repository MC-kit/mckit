"""Intercept log messages from the used libraries and pass them to `loguru`.

See https://github.com/Delgan/loguru
"""

from __future__ import annotations

from typing import Final

import logging
import sys

from os import environ

from loguru import logger

# class PropagateHandler(logging.Handler):
#     """Send events from loguru to standard logging"""
#     def emit(self, record):
#         logging.getLogger(record.name).handle(record)
#
#
# logger.add(PropagateHandler(), format="{message}")


class InterceptHandler(logging.Handler):
    """Send events from standard logging to loguru."""

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


log = logging.getLogger()
log.addHandler(InterceptHandler())


MCKIT_CONSOLE_LOG_FORMAT: Final[str] = environ.get(
    "MCKIT_CONSOLE_LOG_FORMAT",
    default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>",
)


def init_logger(logfile, quiet, verbose, *, stderr_format: str = MCKIT_CONSOLE_LOG_FORMAT):
    stderr_level: str = "INFO"
    if quiet:
        stderr_level = "WARNING"
    elif verbose:
        stderr_level = "TRACE"
    logger.remove()
    if stderr_format:
        logger.add(
            sys.stderr,
            format=stderr_format,
            level=stderr_level,
            backtrace=False,
            diagnose=False,
        )
    if logfile:
        logger.add(logfile, rotation="100 MB", level="TRACE")
