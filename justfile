alias t := test
alias c := check
set dotenv-load := true

default_python := "3.13"
TITLE := `uv version`
VERSION := `uv version --short`

log := "warn"

export JUST_LOG := log

@_default:
  just --list

# git push bypassing pixi-provided openssl libraries
[group: 'dev']
@gp:
  LD_LIBRARY_PATH="" git push

# create venv, if not exists
[group: 'dev']
@venv:
  [ -d .venv ] || uv venv --python {{default_python}} --seed

# download/update submodules 
[group: 'dev']
@submodule: 
  git submodule update --init --recursive --depth 1
  
# build package
[group: 'dev']
@uv_build: submodule venv
  uv build

[group: 'dev']
@build: submodule 
  pixi build

# clean reproducible files
[group: 'dev']
@clean:
  #!/bin/bash
  dirs_to_clean=(
      ".benchmarks"
      ".cache"
      ".eggs"
      ".mypy_cache"
      ".nox"
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
  rm -fr "docs/_build"
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
[group: 'dev']
@install *args: build
  pixi install {{args}}  

# clean build
[group: 'dev']
@reinstall: clean install


# Check style and test
[group: 'dev']
@check: pre-commit test

# Check style includeing mypy and pylint and test
[group: 'dev']
@check-full: check mypy pylint pyright
 
# Bump project version
[group: 'dev']
@bump *args="patch":
  uv version --bump {{args}}
  git commit -m "bump: version $(uv version)" pyproject.toml uv.lock 

# update tools
[group: 'dev']
@up-tools:
  pre-commit autoupdate
  pixi self-update
  pre-commit run -a 

# update dependencies
[group: 'dev']
@up:
  pixi update
  pre-commit run -a 
  pytest

# show dependencies
[group: 'dev']
@tree *args:
  uv tree --outdated {{args}}

# test up to the first fail
[group: 'test']
@test-ff *args:
  pytest -vv -x {{args}}

# test with clean cache
[group: 'test']
@test-cache-clear *args:
  pytest -vv --emoji --cache-clear {{args}}

# test fast
[group: 'test']
@test-fast *args:
  pytest -vv --emoji -m "not slow" {{args}}

# run all the tests
[group: 'test']
@test *args:
  pytest -vv --emoji {{args}}

# run documentation tests 
[group: 'test']
@xdoctest *args:
  uv run --no-dev --group test --group test python -m xdoctest --silent --style google -c all src tools {{args}}

# create coverage data
[group: 'test']
@coverage:
  uv run --no-dev --group test coverage run --parallel -m pytest
  uv run --no-dev --group coverage coverage combine
  uv run --no-dev --group coverage coverage report --show-missing --skip-covered

# coverage to html
[group: 'test']
coverage-html: coverage
  @uv run --no-dev --group coverage coverage html

# check correct typing at runtime
[group: 'test']
typeguard *args:
  @uv run --no-dev --group test --group typeguard pytest -vv --emoji --typeguard-packages=src {{args}}


# ruff check and format
[group: 'lint']
@ruff:
  ruff check --fix src tests
  ruff format src tests

# Run pre-commit on all files
[group: 'lint']
@pre-commit:
  uv run --no-dev --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files

# Run mypy
[group: 'lint']
@mypy:
  uv run --no-dev --group mypy mypy src tests docs/source/conf.py

[group: 'lint']
@pylint:
  uv run --no-dev --group lint pylint --recursive=y src tests

[group: 'lint']
@pyright:
  uv run --no-dev --group pyright pyright src tests

# Check rst-texts
[group: 'docs']
@rstcheck:
  uv run --no-dev --group docs rstcheck --recursive *.rst docs

# build documentation
[group: 'docs']
@docs-build: rstcheck
  uv run --no-dev --group docs sphinx-build docs/source docs/_build

# browse and edit documentation with auto build
[group: 'docs']
@docs:
  uv run --no-dev --group docs --group docs sphinx-autobuild --open-browser docs/source docs/_build
