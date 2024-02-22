"""Try typer CLI."""

from __future__ import annotations

from typing import Annotated, Optional

from pathlib import Path

import typer

from rich.console import Console

app = typer.Typer(rich_markup_mode="rich")
console = Console(stderr=True)

__version__ = "0.1.0"


def version_callback(value: bool):
    if value:
        print(f"Awesome CLI Version: {__version__}")
        raise typer.Exit()


# @app.command()
# def main(
#     name: Annotated[str, typer.Option()] = "World",
#     version: Annotated[Optional[bool], typer.Option("--version", callback=version_callback)] = None,
# ):
#     print(f"Hello {name}")

# @app.command()
# def main():
#     print("Opening Typer's docs")
#     typer.launch("https://typer.tiangolo.com")

# APP_NAME = "my-super-cli-app"
#
# @app.command()
# def main():
#     app_dir = typer.get_app_dir(APP_NAME)
#     app_dir_path = Path(app_dir)
#     console.print(app_dir_path)


@app.command()
def main(name: str = "morty"):
    print(name + 3)


if __name__ == "__main__":
    app()
