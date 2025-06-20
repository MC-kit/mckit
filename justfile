set dotenv-load := true

default:
  @just --list

test-ff *ARGS:
  pytest -vv -x {{ARGS}}

test-cache-clear *ARGS:
  pytest -vv --cache-clear {{ARGS}}

test-fast *ARGS:
  pytest -m "not slow" {{ARGS}}

test-all *ARGS:
  pytest {{ARGS}}

# Clean reproducible files
clean:
  #!/bin/bash
  to_clean=(
      ".benchmarks"
      ".eggs"
      ".mypy_cache"
      ".nox"
      ".pytest_cache"
      ".cache"
      ".ruff_cache"
      "__pycache__"
      "_skbuild"
      "build"
      "htmlcov"
      "setup.py"
      "docs/_build"
  )
  rm -fr ${to_clean[@]}


build:
  poetry build
  poetry install  

# Clean build
rebuild: clean build


alias t := test-all
