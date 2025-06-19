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

alias t := test-all

