from __future__ import annotations

import pytest

from mckit.printer import pretty_float, print_card, separate


@pytest.mark.parametrize(
    "tokens, sep, expected",
    [
        (["1", "2", "3"], " ", ["1", " ", "2", " ", "3"]),
        (["1"], " ", ["1"]),
        (["a", "b", "c", "d"], "  ", ["a", "  ", "b", "  ", "c", "  ", "d"]),
        (["A", "B"], "   ", ["A", "   ", "B"]),
    ],
)
def test_separate(tokens, sep, expected):
    new_tokens = separate(tokens, sep=sep)
    assert new_tokens == expected


@pytest.mark.parametrize(
    "words, offset, max_col, sep, expected",
    [
        (
            ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
            5,
            13,
            "\n",
            "There is  a \n     word   \n     in   \n     here",
        ),
        # (
        #     ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
        #     4,
        #     13,
        #     "\n",
        #     "There is  a \n     word   \n     in   \n     here",
        # ),
        (
            ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
            5,
            14,
            "\n",
            "There is  a \n     word   in\n     here",
        ),
        (
            ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
            5,
            16,
            "\n",
            "There is  a word\n     in   here",
        ),
        (
            ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
            6,
            16,
            "\n",
            "There is  a word\n      in   here",
        ),
        (
            ["There", " ", "is", "  ", "a", " ", "word", "   ", "in", "   ", "here"],
            5,
            80,
            "\n",
            "There is  a word   in   here",
        ),
        (
            [
                "There",
                " ",
                "is",
                "  ",
                "a",
                "\n",
                " ",
                "word",
                "   ",
                "in",
                "   ",
                "here",
            ],
            5,
            80,
            "\n",
            "There is  a\n     word   in   here",
        ),
        (
            [
                "There",
                " ",
                "is",
                "  ",
                "a",
                " ",
                "\n",
                "word",
                "   ",
                "in",
                "   ",
                "here",
            ],
            5,
            80,
            "\n",
            "There is  a \n     word   in   here",
        ),
        (
            [
                "There",
                " ",
                "is",
                "  ",
                "a",
                "|",
                " ",
                "word",
                "   ",
                "in",
                "   ",
                "here",
            ],
            5,
            80,
            "|",
            "There is  a\n     word   in   here",
        ),
        (
            [
                "There",
                " ",
                "is",
                "  ",
                "a",
                " ",
                "%",
                "word",
                "   ",
                "in",
                "   ",
                "here",
            ],
            5,
            80,
            "%",
            "There is  a \n     word   in   here",
        ),
    ],
)
def test_print_card(words, offset, max_col, sep, expected):
    card = print_card(words, offset, max_col, sep)
    assert card == expected


@pytest.mark.parametrize(
    "value, sig_digits, answer",
    [
        (5.432e0, 3, "5.432"),
        (5.432e1, 2, "54.32"),
        (5.432e2, 1, "543.2"),
        (5.432e3, 0, "5432"),
        (5.432e4, 0, "54320"),
        (5.432e5, -3, "543000"),
        (5.432e6, -3, "5432000"),
        (5.432e7, -4, "54320000"),
        (5.432e8, -5, "543200000"),
        (5.432e9, -6, "5.432e+09"),
        (5.432e-1, 4, "0.5432"),
        (5.432e-2, 5, "0.05432"),
        (5.432e-3, 6, "0.005432"),
        (5.432e-4, 7, "0.0005432"),
        (5.432e-5, 8, "5.432e-05"),
        (5.432e-6, 9, "5.432e-06"),
        (1.0e-12, 14, "1.0e-12"),
        (1.0e-14, 15, "1e-14"),
        (0.0e0, 1, "0.0"),
        (0.0e0, 0, "0"),
        (-5.432e0, 3, "-5.432"),
        (-5.432e1, 2, "-54.32"),
        (-5.432e2, 1, "-543.2"),
        (-5.432e3, 0, "-5432"),
        (-5.432e4, -1, "-54320"),
        (-5.432e5, -2, "-543200"),
        (-5.432e6, -3, "-5432000"),
        (-5.432e7, -4, "-54320000"),
        (-5.432e8, -5, "-543200000"),
        (-5.432e9, -6, "-5.432e+09"),
        (-5.432e-1, 4, "-0.5432"),
        (-5.432e-2, 5, "-0.05432"),
        (-5.432e-3, 6, "-0.005432"),
        (-5.432e-4, 7, "-0.0005432"),
        (-5.432e-5, 8, "-5.432e-05"),
        (-5.432e-6, 9, "-5.432e-06"),
        (-1.0e-12, 14, "-1.0e-12"),
        (-1.0e-14, 15, "-1e-14"),
        (-0.0e0, 1, "0.0"),
        (-0.0e0, 0, "0"),
        (1.0, 1, "1.0"),
        (-1.0, 1, "-1.0"),
        (1.0, 2, "1.00"),
        (1.0001, 1, "1.0"),
        (0.9999, 1, "1.0"),
        (2.142936012882e05, 0, "214294"),
        (2.142936012882e05, 1, "214293.6"),
        (3.142936012882e05, 2, "314293.60"),
        (4.142936012882e05, 3, "414293.601"),
        (5.142936012882e05, 1, "514293.6"),
        (6.142936012882e05, 1, "614293.6"),
        (-7.142936012882e05, 1, "-714293.6"),
        (8.142936012882e05, -2, "814300"),
        (9.142936012882e05, 1, "914293.6"),
        (1.142936012882e05, 1, "114293.6"),
    ],
)
def test_pretty_float(value, sig_digits, answer):
    text = pretty_float(value, sig_digits)
    assert text == answer
