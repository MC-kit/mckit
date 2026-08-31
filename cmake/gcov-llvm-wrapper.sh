#!/bin/bash
# Modern CMake for C++, p.303
# Wrapper for clang coverage
exec llvm-cov gcov "$@"