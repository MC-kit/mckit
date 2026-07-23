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

# show version
[group('dev')]
@version:
    uv version

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
    pixi publish --target-channel file://$(pwd)/.output

# clean reproducible files
[group('dev')]
@clean:
    #!/bin/bash
    dirs_to_clean=(
        ".benchmarks"
        ".cache"
        ".eggs"
        ".mypy_cache"
        ".output"
        ".output-py314"
        ".pixi"
        ".pytest_cache"
        ".ruff_cache"
        ".sk-build"
        ".venv"
        "_build"
        "build"
        "cmake-build-debug"
        "dist"
        "docs/_build"
        "htmlcov"
    )
    for d in "${dirs_to_clean[@]}"; do
       [ -d "$d" ] && echo "removing $d" && rm -fr "$d" 
    done
    dirs_to_clean=(
        "__pycache__"
    )
    for d in "${dirs_to_clean[@]}"; do
        find . -type d -wholename "$d" -exec rm -rf {} +
    done
    files_to_clean=(
        "*.so"
        "*.so.*"
        "*.dll"
        "*.dylib"
    )
    for f in "${files_to_clean[@]}"; do
        find src/mckit -type f -name "$f" -exec rm -f {} +
    done
    # pixi clean
    coverage erase
    #pyreverse files
    find . -type f -name "*.puml" -delete

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
@check-full: check ty basedpyright pyrefly pylint

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
    pixi tree {{ args }}

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
    pixi run test-fast {{ args }}

# test slow
[group('test')]
@test-slow *args:
    pixi run test-slow {{ args }}

# run all the tests
[group('test')]
@test *args:
    pixi run test {{ args }}

# run documentation tests
[group('test')]
@xdoctest *args:
    xdoctest --silent -c all -m mckit {{ args }}

# create coverage data
[group('test')]
@coverage:
    pixi run coverage

# coverage to html
[group('test')]
@coverage-html:
    # uv run --no-dev --group test pytest --cov --cov-report html:htmlcov
    pixi run coverage-html
    open htmlcov/index.html

# check correct typing at runtime
[group('test')]
typeguard *args:
    # @uv run --no-dev --group test --group typeguard pytest --typeguard-packages=src {{ args }}
    pixi run typeguard {{ args }}

# ruff check and format
[group('style')]
@ruff:
    ruff check --fix src tests
    ruff format src tests

# Run pre-commit on all files
[group('style')]
@pre-commit:
    pre-commit run --show-diff-on-failure --color=always --all-files

# Run mypy
[group('style')]
@mypy:
    mypy src tests docs/source/conf.py

[group('style')]
@pylint:
    pylint --recursive=y --output-format colorized src tests

[group('style')]
@pyright:
    pyright

# Lint with ty
[group('style')]
@ty:
    ty check 

[group('style')]
@basedpyright:
    basedpyright

[group('style')]
@pyrefly *args="check":
    pyrefly {{ args }}

# Draw UML diagrams
[group('style')]
@pyreverse:
    pyreverse --project mckit --colorized --output puml --output-directory .pyreverse --ignore data --source-roots src/**/*.py

# Find code duplicates
[group('style')]
@symilar:
    uv run --no-dev --group lint symilar src/**/*.py

# Check rst-texts
[group('docs')]
@rstcheck:
    rstcheck --recursive *.rst docs

# build documentation
[group('docs')]
@docs-build: # rstcheck
    pixi run docs-build

# browse and edit documentation with auto build
[group('docs')]
@docs:
   pixi run docs 
