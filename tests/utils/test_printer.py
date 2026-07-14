from __future__ import annotations

import pytest

from mckit.printer import print_option

@pytest.mark.parametrize(
    "opt, val, expected",
    [
        ("IMPN", 1.0, ["IMP:N=1"]),
        ("VOL", 1.0, ["VOL=1" ]),
        ("PMT", 0, ["PMT=0"]),
        ("FCLN", 1, ["FCL:N=1"]),
    ],
)
def test_parser_with_attributes(opt, val, expected):
    actual = print_option(opt, val)
    assert actual == expected
