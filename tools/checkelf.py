# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cmake",
#     "lief",
# ]
# ///
"""Check ELF file for security.

Example from https://habr.com/en/companies/inforion/articles/460247.
obsidian://open?vault=work&file=%D0%A0%D0%B5%D1%86%D0%B5%D0%BF%D1%82%D1%8B%20%D0%B4%D0%BB%D1%8F%20ELF%D0%BE%D0%B2

LIEF is avaiable on PyPI, and conda-forge (as py-lief).

The code is not runnable. Need to fix. Use as an example only.

"""

from __future__ import annotations

import lief

from lief.ELF import DYNAMIC_TAGS, SEGMENT_TYPES


def filecheck(filename):
    binary = lief.parse(filename)

    # check RELRO
    if binary.has(SEGMENT_TYPES.GNU_RELRO):
        print("+ Full RELRO") if binary.has(DYNAMIC_TAGS.BIND_NOW) else print("~ Partial RELRO")
    else:
        print("- No RELRO")

    # check for stack canary support
    print("+ Canary found") if binary.has_symbol("__stack_chk_fail") else print("- No canary found")

    # check for NX support (check X-flag for GNU_STACK-segment)
    print("+ NX enabled") if binary.has_nx else print("- NX disabled")

    # check for PIE support
    print("+ PIE enabled") if binary.is_pie else print("- No PIE")

    # check for rpath / run path
    print("+ RPATH") if binary.has(DYNAMIC_TAGS.RPATH) else print("- No RPATH")
    print("+ RUNPATH") if binary.has(DYNAMIC_TAGS.RUNPATH) else print("- No RUNPATH")

    # check separate-code option
    if set(binary.get_section(".text").segments) == set(binary.get_section(".rodata").segments):
        print("- Not Separated Code Sections")
    else:
        print("+ Separated Code Sections")


filecheck("test_rpath.elf")
