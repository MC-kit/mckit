from __future__ import annotations

from io import StringIO
from pathlib import Path

import click

from mckit.cli._logging import logger
from mckit.constants import MCNP_ENCODING
from mckit.universe import Universe, UniverseAnalyser

# This is the encoding swallowing non ascii (neither unicode) symbols happening in MCNP models code


def check_if_path_exists(path: str | Path, override: bool):
    if isinstance(path, str):
        path = Path(path)
    if not override and path.exists():
        errmsg = f"""\
        Cannot override existing file \"{path}\".
        Please remove the file or specify --override option"""
        logger.error(errmsg)
        raise click.UsageError(errmsg)


def save_mcnp(model: Universe, path: str | Path, override: bool):
    check_if_path_exists(path, override)
    analyser = UniverseAnalyser(model)
    if analyser.we_are_all_clear():
        model.save(path, encoding=MCNP_ENCODING, check_clashes=False)
    else:
        out = StringIO()
        out.write("Duplicates found:\n")
        analyser.print_duplicates_map(stream=out)
        raise ValueError(out.getvalue())


def get_default_output_directory(source, suffix):
    return Path(Path(source).with_suffix(suffix).name)
