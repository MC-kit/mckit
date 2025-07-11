alias t := test
alias c := check
set dotenv-load := true

default_python := "3.13"
TITLE := `uv version`
VERSION := `uv version --short`

log := "warn"

export JUST_LOG := log

default:
  @just --list

# create venv, if not exists
[group: 'dev']
venv:
  [ -d .venv ] || uv venv --python {{default_python}}

# build package
[group: 'dev']
build: venv
  uv build

# clean reproducible files
[group: 'dev']
clean:
  #!/bin/bash
  to_clean=(
      ".benchmarks"
      ".cache"
      ".eggs"
      ".mypy_cache"
      ".nox"
      ".pytest_cache"
      ".ruff_cache"
      ".venv"
      "__pycache__"
      "_skbuild"
      "build"
      "dist"
      "docs/_build"
      "htmlcov"
      "setup.py"
  )
  rm -fr ${to_clean[@]}


# install package
[group: 'dev']
install: build
  uv sync   

# clean build
[group: 'dev']
reinstall: clean install


# Check style and test
[group: 'dev']
check: pre-commit test

[group: 'dev']
@bump *args:
  #!/bin/bash
  uv version --bump {{args}}
  git commit -m "bump: version $(uv version)" pyproject.toml uv.lock 

# update dependencies
[group: 'dev']
@up:
  pre-commit autoupdate
  uv self update

# ruff check and format
[group: 'dev']
@ruff:
  ruff check --fix src tests
  ruff format src tests

# test up to the first fail
[group: 'test']
test-ff *args:
  @pytest -vv -x {{args}}

# test with clean cache
[group: 'test']
test-cache-clear *args:
  @pytest -vv --emoji --cache-clear {{args}}

# test fast
[group: 'test']
test-fast *args:
  @pytest -vv --emoji -m "not slow" {{args}}

# run all the tests
[group: 'test']
test *args:
  @pytest -vv --emoji {{args}}

# run documentation tests 
[group: 'test']
xdoctest *args:
  @uv run --no-dev --group test --group xdoctest python -m xdoctest --silent --style google -c all src tools {{args}}

# create coverage data
[group: 'test']
coverage:
  @uv run --no-dev --group coverage coverage run --parallel -m pytest
  @uv run --no-dev --group coverage coverage combine
  @uv run --no-dev --group coverage coverage report

# coverage to html
[group: 'test']
coverage-html: coverage
  @uv run --no-dev --group coverage coverage html

# check correct typing at runtime
[group: 'test']
typeguard *args:
  @uv run --no-dev --group test --group typeguard pytest -vv --emoji --typeguard-packages=src {{args}}


# Run pre-commit on all files
[group: 'lint']
pre-commit:
  @uv run --no-dev --group pre-commit pre-commit run -a 

# Run mypy
[group: 'lint']
mypy:
  @uv run --no-dev --group mypy mypy src docs/source/conf.py

# Check rst-texts
[group: 'docs']
rstcheck:
  @rstcheck *.rst docs/source/*.rst

# build documentation
[group: 'docs']
docs-build: rstcheck
  @uv run --no-dev --group docs sphinx-build docs/source docs/_build

# browse and edit documentation with auto build
docs:
  @uv run --no-dev --group docs --group docs-auto sphinx-autobuild --open-browser docs/source docs/_build
