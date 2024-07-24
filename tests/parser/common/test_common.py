from __future__ import annotations

import re

import pytest

import mckit.parser.common.utils as m


@pytest.mark.parametrize(
    "text,expected",
    [
        ("a\nc\nb", "a\nb"),
        (
            """m1
 c some comment
        1001.21c -1.0
        """,
            """m1
        1001.21c -1.0
        """,
        ),
        (
            """
(
   a
)
c
(
   b
)
""",
            """
(
   a
)
(
   b
)
""",
        ),
    ],
)
def test_drop_c_comments(text, expected):
    actual = m.drop_c_comments(text)
    assert actual == expected


def test_when_no_c_comments_in_text():
    text = """m1
    1001.21c -1.0
    """
    actual = m.drop_c_comments(text)
    assert actual is text, "drop_c_comments should return the text object without changes"


RE_FLOAT = re.compile(m.FLOAT)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1", "1"),
        (" 0.1", "0.1"),
        (".2\n", ".2"),
        ("\n -1e10a", "-1e10"),
        ("0.", "0."),
    ],
)
def test_float_pattern(text, expected):
    match = RE_FLOAT.search(text)
    assert match, "Should find float number in the text"
    actual = match.group()
    assert actual == expected


@pytest.mark.parametrize(
    "text, expected_new_text, expected_comments, expected_trailing_comment",
    [
        ("1 $ zzz", "1 ", {1: ("zzz",)}, None),
        ("1 $ zzz\n $ ttt", "1 ", {1: ("zzz",)}, ["ttt"]),
        ("1\n $ ttt", "1", None, ["ttt"]),
        ("1 $ zzz\n $ ttt\n2", "1 \n2", {1: ("zzz", "ttt")}, None),
        (
            """M1000
1001.21c -1.0
    gas 1
    $ trailing comment1
    $ trailing comment2
""",
            """M1000
1001.21c -1.0
    gas 1
""",
            None,
            ["trailing comment1", "trailing comment2"],
        ),
    ],
)
def test_extract_comments(text, expected_new_text, expected_comments, expected_trailing_comment):
    actual_new_text, actual_comments, actual_trailing_comment = m.extract_comments(text)
    assert actual_new_text == expected_new_text
    assert actual_comments == expected_comments
    assert actual_trailing_comment == expected_trailing_comment
