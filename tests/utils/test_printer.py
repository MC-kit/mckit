from __future__ import annotations

import pytest

import mckit.printer as m

from mckit.printer import print_option


@pytest.mark.parametrize(
    "opt, val, expected",
    [
        ("IMPN", 1.0, ["IMP:N=1"]),
        ("VOL", 1.0, ["VOL=1"]),
        ("PMT", 0, ["PMT=0"]),
        ("FCLN", 1, ["FCL:N=1"]),
    ],
)
def test_parser_with_attributes(opt, val, expected):
    actual = print_option(opt, val)
    assert actual == expected


def test_print_option_not_implemented():
    with pytest.raises(ValueError, match="Not implemented option name"):
        print_option("XX", 1)


def test_print_card_limits():
    tokens = ["1", " ", "PX", " ", "0", "\n"]
    actual = m.print_card(tokens, offset=4, max_column=100)
    expected = m.print_card(["1", " ", "PX", " ", "0"], offset=5, max_column=80)
    assert actual == expected


@pytest.mark.parametrize(
    "frac_digits, value, expected",
    [
        (2, 123.456, "123.46"),
    ],
)
def test_pretty_float(frac_digits, value, expected):
    assert m.pretty_float(value, frac_digits) == expected


def test_pretty_float_negative_zero():
    assert m.pretty_float(-0.0, 1) == "0.0"


def test_pretty_float_zero_digits():
    assert m.pretty_float(1.11, 0) == "1"


@pytest.mark.parametrize(
    "value, pretty, expected",
    [
        (1.23, True, m.pretty_float(1.23)),
        (1.23, False, m.prettify_float(1.23)),
    ],
)
def test_add_float(value, pretty, expected):
    words = []
    m.add_float(words, value, pretty)
    assert words == [" ", expected]
