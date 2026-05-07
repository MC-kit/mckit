# Examples: msgspec

# Disable showing recipe lines before execution.
set quiet

# Enable unstable features.
set unstable

# Configure the shell for Windows.
set windows-shell := ["pwsh.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"]

# We don't want to install any dev dependencies by default.
# export UV_NO_DEV := "true"

alias t := test
alias c := check
set dotenv-load

default_python := "3.13"
TITLE := `uv version`
VERSION := `uv version --short`

log := "warn"

export JUST_LOG := log

@_default:
    just --list

# git push bypassing pixi-provided openssl libraries
[group('dev')]
@gp:
    LD_LIBRARY_PATH="" git push

# create venv, if not exists
[group('dev')]
@venv:
    [ -d .venv ] || uv venv --python {{ default_python }} --seed

# build package
[group('dev')]
@uv_build: venv
    uv build

# check distribution with twine
[group('dev')]
@check-dist: build
    uvx twine check dist/*

# build conda package
[group('dev')]
@build:
    pixi build --output-dir .output

# clean reproducible files
[group('dev')]
@clean:
    #!/bin/bash
    dirs_to_clean=(
        ".benchmarks"
        ".cache"
        ".eggs"
        ".mypy_cache"
        ".pytest_cache"
        ".ruff_cache"
        ".venv"
        "__pycache__"
        "_build"
        "build"
        "cmake-build-debug"
        "dist"
        "docs/_build"
        "htmlcov"
    )
    for d in "${dirs_to_clean[@]}"; do
        find . -type d -wholename "$d" -exec rm -rf {} +
    done
    files_to_clean=(
        "*.so"
        "*.so.*"
        "*.dll"
        "*.dylib"
        "setup.py"
    )
    for f in "${files_to_clean[@]}"; do
        find src/mckit -type f -name "$f" -exec rm -f {} +
    done
    pixi clean

# install package
[group('dev')]
@install *args: build
    pixi install {{ args }}  

# clean build
[group('dev')]
@reinstall: clean install

# Check style and test
[group('dev')]
@check: pre-commit test

# Check style includeing mypy and pylint and test
[group('dev')]
@check-full: check mypy pylint pyright

# Bump project version  # TODO dvp: revise for pixi
[group('dev')]
@bump *args="patch":
    uv version --bump {{ args }}
    git commit -m "bump: version $(uv version)" pyproject.toml uv.lock 

# update tools
[group('dev')]
@up-tools:
    pre-commit autoupdate
    pixi self-update
    pre-commit run -a 

# update dependencies
[group('dev')]
@up:
    pixi update
    pre-commit run -a 
    pytest

# show dependencies
[group('dev')]
@tree *args:
    uv tree --outdated {{ args }}

# run pyupgrade
[group('dev')]
@pyupgrade *args="--py314-plus":
    uvx pyupgrade {{ args }}  # presumably, code is updated by ruff, just to check sometimes

# test up to the first fail
[group('test')]
@test-ff *args:
    pytest -vv -x {{ args }}

# test with clean cache
[group('test')]
@test-cache-clear *args:
    pytest --cache-clear {{ args }}

# test fast
[group('test')]
@test-fast *args:
    pytest -m "not slow" {{ args }}

# run all the tests
[group('test')]
@test *args:
    pytest {{ args }}

# run documentation tests
[group('test')]
@xdoctest *args:
    uv run --no-dev --group test --group test xdoctest --silent -c all -m mckit {{ args }}

# create coverage data
[group('test')]
@coverage:
    uv run --no-dev --group test pytest --cov --cov-report=term-missing:skip-covered

# coverage to html
[group('test')]
@coverage-html:
    uv run --no-dev --group test pytest --cov --cov-report html:htmlcov
    open htmlcov/index.html

# check correct typing at runtime
[group('test')]
typeguard *args:
    @uv run --no-dev --group test --group typeguard pytest --typeguard-packages=src {{ args }}

# ruff check and format
[group('lint')]
@ruff:
    ruff check --fix src tests
    ruff format src tests

# Run pre-commit on all files
[group('lint')]
@pre-commit:
    uv run --no-dev --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files

# Run mypy
[group('lint')]
@mypy:
    uv run --no-dev --group mypy mypy src tests docs/source/conf.py

[group('lint')]
@pylint:
    uv run --no-dev --group lint pylint --recursive=y --output-format colorized src tests

[group('lint')]
@pyright:
    uv run --no-dev --group pyright pyright src tests

# Lint with ty
[group('lint')]
@ty:
    uvx ty check 

# Check rst-texts
[group('docs')]
@rstcheck:
    uv run --no-dev --group docs rstcheck --recursive *.rst docs

# build documentation
[group('docs')]
@docs-build: rstcheck
    uv run --no-dev --group docs sphinx-build docs/source docs/_build

# browse and edit documentation with auto build
[group('docs')]
@docs:
    uv run --no-dev --group docs --group docs sphinx-autobuild --open-browser docs/source docs/_build
