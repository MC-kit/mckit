from __future__ import annotations

import re

from io import StringIO

import pytest

import mckit.parser.mcnp_section_parser as sp

from mckit.parser.mcnp_section_parser import Card, Kind


@pytest.mark.parametrize(
    "text,expected",
    [
        ("aaa\n\nbbb", ["aaa", "bbb"]),
        ("aaa\n   \nbbb", ["aaa", "bbb"]),
        ("aaa\nbbb", ["aaa\nbbb"]),
    ],
)
def test_blank_line_pattern(text: str, expected: list[str]) -> None:
    actual = sp.BLANK_LINE_PATTERN.split(text)
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 0 1\n", ("1 0 1\n", 0)),
        ("1 0 1 $bla bla bla\n", ("1 0 1\n", 1)),
        (
            "1 0 1 $bla bla bla\n" + "c the comment with the space before c\n" + "   2 -3",
            ("1 0 1\n" + "   2 -3", 2),
        ),
    ],
)
def test_removing_comment_pattern(text, expected):
    actual = sp.REMOVE_COMMENT_PATTERN.subn("", text)
    assert expected == actual


@pytest.mark.parametrize(
    "text,comment,card",
    [
        ("1 0 1\n", None, "1 0 1\n"),
        (
            """\
c the preceding comment
1 0 1""",
            """\
c the preceding comment
""",
            "1 0 1",
        ),
        (
            """\
c the preceding comment
1 0 1
 c The next card comment (with space before it)
  2 $next card""",
            """\
c the preceding comment
""",
            "1 0 1\n",
        ),
        (
            """\
C ----------------------------------------------------------------------------C
C    TRANSFORMATIONS                                                          C
C    ROTATION WITH RESPECT TO Z-AXIS (-20,|5|,20)                             C
C ----------------------------------------------------------------------------C
*TR1    0  0  0
        20.0000    70.0000  90
       110.0000    20.0000  90
       90        90         0""",
            """\
C ----------------------------------------------------------------------------C
C    TRANSFORMATIONS                                                          C
C    ROTATION WITH RESPECT TO Z-AXIS (-20,|5|,20)                             C
C ----------------------------------------------------------------------------C
""",
            """\
*TR1    0  0  0
        20.0000    70.0000  90
       110.0000    20.0000  90
       90        90         0""",
        ),
    ],
)
def test_card_pattern(text, comment, card):
    res = sp.CARD_PATTERN.match(text)
    groups = res.groupdict()
    actual_comment = groups["comment"]
    assert comment == actual_comment
    actual_card = groups["card"]
    assert actual_card == card


@pytest.mark.parametrize(
    "text,expected,tag,number",
    [
        ("f1", "f1", "f", 1),
        ("FMESH10", "FMESH10", "FMESH", 10),
        ("fm999", "fm999", "fm", 999),
        ("fc1", "fc1", "fc", 1),
        ("de1", "de1", "de", 1),
        ("df1", "df1", "df", 1),
    ],
)
def test_tally_pattern(text: str, expected: str, tag: str, number: int) -> None:
    res = sp.TALLY_PATTERN.fullmatch(text)
    actual = res.group(0) if res else None
    assert actual == expected, f"Should match pattern '{text}'"
    actual_tag = res["tag"]
    assert actual_tag == tag, "Tags differ"
    actual_number = int(res["number"])
    assert actual_number == number, "Numbers differ"


@pytest.mark.parametrize("text", ["f", "111"])
def test_tally_pattern_bad_path(text: str) -> None:
    res = sp.TALLY_PATTERN.fullmatch(text)
    assert res is None, f"Should not match pattern '{text}'"


@pytest.mark.parametrize(
    "text,cards,kind",
    [
        (
            """
c the preceding comment
1 0 1
c next comment
  2 $next card (starts with less than 5 spaces)
"""[1:-1],
            [
                Card("c the preceding comment"),
                Card("1 0 1", kind=Kind.CELL),
                Card("c next comment"),
                Card("  2 $next card (starts with less than 5 spaces)", kind=Kind.CELL),
            ],
            Kind.CELL,
        ),
        (
            """
c the preceding comment
1 0 1
c inner comment
     2 $continuation
c the second preceding comment
2 0 -1 $the next card
c the trailing comment
c the second line of the trailing comment
"""[1:-1],
            [
                Card("c the preceding comment"),
                Card(
                    """
1 0 1
c inner comment
     2 $continuation
"""[1:-1],
                    kind=Kind.CELL,
                ),
                Card("c the second preceding comment"),
                Card("2 0 -1 $the next card", kind=Kind.CELL),
                Card(
                    """
c the trailing comment
c the second line of the trailing comment
"""[1:-1]
                ),
            ],
            Kind.CELL,
        ),
        (
            """
  cut 5j  $ card starts in column < 5
ctme 3000
"""[1:],
            [Card("  cut 5j  $ card starts in column < 5"), Card("ctme 3000")],
            None,
        ),
        (
            """
m100
      1001.31c 0.6666
      8000.21c 0.3334
"""[1:-1],
            [
                Card(
                    """
m100
      1001.31c 0.6666
      8000.21c 0.3334
"""[1:-1],
                    kind=Kind.MATERIAL,
                )
            ],
            None,
        ),
    ],
)
def test_split_to_cards(text, cards, kind):
    actual_cards = list(sp.split_to_cards(text, kind))
    assert actual_cards == cards


@pytest.mark.parametrize(
    "text",
    [
        (
            """
sdef
sp1
si1
ds3
sb45
wwp:n
"""[1:-1]
        )
    ],
)
def test_sdef_cards(text):
    actual_cards = list(sp.split_to_cards(text))
    for card in actual_cards:
        assert card.is_sdef, "Should be SDEF card"


def test_card_constructor():
    description = "1 0 1"
    c = Card(description)
    assert c.text == description


def test_input_sections_constructor():
    title = "Testing"
    cell_cards = [Card("1 0 1"), Card("2 0 -1")]
    surface_cards = [Card("1 so 100")]
    t = sp.InputSections(title, cell_cards, surface_cards, [Card("sdef")])
    assert t.title == title


@pytest.mark.parametrize(
    "text,expected,kind",
    [
        (
            """
1 0 1 $bla bla bla
"""[1:-1],
            [Card("1 0 1", kind=Kind.CELL)],
            Kind.CELL,
        ),
        (
            """
c some comment
c second line
1 0 1 $bla bla bla
     2 $continuation
c trailing comment
"""[1:-1],
            [
                Card(
                    """
1 0 1 2
"""[1:-1],
                    kind=Kind.CELL,
                )
            ],
            Kind.CELL,
        ),
        (
            """
c some comment
c second line
1 0 1 $bla bla bla
     2 $continuation
c trailing comment
2
     0 -1  $something
c z-z-zz-z-z-z
"""[1:-1],
            [
                Card(
                    """
1 0 1 2
"""[1:-1],
                    kind=Kind.CELL,
                ),
                Card(
                    """
2 0 -1
"""[1:-1],
                    kind=Kind.CELL,
                ),
            ],
            Kind.CELL,
        ),
    ],
)
def test_clean_mcnp_cards(text, expected, kind):
    actual = list(sp.clean_mcnp_cards(sp.split_to_cards(text, kind)))
    assert actual == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            """
test
1 0 1 $bla bla bla

1 so 1

sdef
"""[1:],
            None,
        ),
        (
            """
test
c some comment
c second line
1 0 1 $bla bla bla
     2 $continuation
2 0 -1
c trailing comment

1 so 1

sdef
"""[1:],
            None,
        ),
        (
            """
test
c some comment
c second line
1 0 1 $bla bla bla
     2 $continuation
c trailing comment
2
    0 -1  $something
c z-z-zz-z-z-z

1 so 1

sdef
"""[1:],
            None,
        ),
        (
            """
continue
ctme 3000
"""[1:],
            None,
        ),
    ],
)
def test_print(text, expected):
    stream = StringIO(text)
    sections = sp.parse_sections(stream)
    out = StringIO()
    sections.print(out)
    if expected is None:
        expected = text.strip()
    actual = out.getvalue().strip()
    assert actual == expected


def test_card_is_cell_and_is_surface() -> None:
    cell = Card("1 0 1", kind=Kind.CELL)
    surface = Card("1 so 100", kind=Kind.SURFACE)
    assert cell.is_cell
    assert not cell.is_surface
    assert surface.is_surface
    assert not surface.is_cell


def test_card_str() -> None:
    assert str(Card("1 0 1")) == "1 0 1"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 0 1", "1"),
        ("*2 so 100", "*2"),
        ("tr5", "tr5"),
    ],
)
def test_card_name(text: str, expected: str) -> None:
    assert Card(text).name == expected


def test_card_name_raises_for_comment() -> None:
    with pytest.raises(AssertionError, match="Comment cannot have name"):
        _ = Card("c hello", kind=Kind.COMMENT).name


@pytest.mark.parametrize(
    "text,kind,expected",
    [
        ("1 0 1", Kind.CELL, 1),
        ("1 so 100", Kind.SURFACE, 1),
        ("*2 so 100", Kind.SURFACE, 2),
        ("m100", Kind.MATERIAL, 100),
        ("tr5", Kind.TRANSFORMATION, 5),
        ("*tr5", Kind.TRANSFORMATION, 5),
    ],
)
def test_card_number(text: str, kind: Kind, expected: int) -> None:
    assert Card(text, kind=kind).number == expected


def test_card_number_raises_for_sdef() -> None:
    with pytest.raises(
        NotImplementedError,
        match=re.escape("Cannot define number for 5 card 'sdef'"),
    ):
        _ = Card("sdef", kind=Kind.SDEF).number


@pytest.mark.parametrize(
    "kwargs,message",
    [
        (
            {"cell_cards": [Card("1 0 1")], "data_cards": [Card("sdef")]},
            "Cells and Surfaces shouldn't present in 'continue' mode model",
        ),
        (
            {},
            "At least one data card should present in 'continue' mode model",
        ),
    ],
)
def test_input_sections_continue_mode_validation(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        sp.InputSections("t", is_continue=True, **kwargs)


def test_input_sections_print_without_cell_cards() -> None:
    sections = sp.InputSections(title="t", surface_cards=[Card("1 so 1")])
    with pytest.raises(ValueError, match="No cell cards"):
        sections.print(StringIO())


def test_input_sections_print_without_surface_cards() -> None:
    sections = sp.InputSections(title="t", cell_cards=[Card("1 0 1")])
    with pytest.raises(ValueError, match="No surface cards"):
        sections.print(StringIO())


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        (
            {
                "title": None,
                "cell_cards": [Card("1 0 1")],
                "surface_cards": [Card("1 so 1")],
                "data_cards": None,
                "remainder": "c tail",
            },
            "1 0 1\n\n1 so 1\n\nc tail\n",
        ),
        (
            {
                "title": "t",
                "cell_cards": [Card("1 0 1")],
                "surface_cards": [Card("1 so 1")],
                "data_cards": [Card("sdef")],
                "message": "msg block",
                "remainder": "c tail",
            },
            "msg block\n\nt\n1 0 1\n\n1 so 1\n\nsdef\n\nc tail\n",
        ),
    ],
)
def test_input_sections_print_optional_parts(kwargs: dict, expected: str) -> None:
    out = StringIO()
    sp.InputSections(**kwargs).print(out)
    assert out.getvalue() == expected


def test_parse_sections_with_message_block() -> None:
    sections = sp.parse_sections_text(
        "message: some\nmsg lines\n\ntitle here\n1 0 1\n\n1 so 1\n\nsdef\n\nthe end\n"
    )
    assert sections.message == "message: some\nmsg lines"
    assert sections.title == "title here"
    assert [c.text for c in sections.cell_cards] == ["1 0 1"]
    assert [c.text for c in sections.surface_cards] == ["1 so 1"]
    assert [c.text for c in sections.data_cards] == ["sdef"]
    assert sections.remainder == "the end\n"
    assert not sections.is_continue


def test_parse_sections_empty_title_raises() -> None:
    with pytest.raises(ValueError, match="Cannot find the MCNP model title"):
        _ = sp.parse_sections_text("\n1 so 1")


def test_parse_continue_sections_with_remainder() -> None:
    sections = sp.parse_sections_text("continue\nm100\n\nextra stuff\n")
    assert sections.is_continue
    assert sections.title == "continue"
    assert [c.text for c in sections.data_cards] == ["m100"]
    assert sections.cell_cards is None
    assert sections.surface_cards is None
    assert sections.remainder == "extra stuff\n"


def test_parse_sections_cells_only() -> None:
    sections = sp.parse_sections_text("title\n1 0 1")
    assert [c.text for c in sections.cell_cards] == ["1 0 1"]
    assert sections.surface_cards is None
    assert sections.data_cards is None
    assert sections.remainder is None


def test_parse_sections_with_remainder() -> None:
    sections = sp.parse_sections_text("title\n1 0 1\n\n1 so 1\n\nsdef\n\nleftover\nmore")
    assert sections.remainder == "leftover\nmore"


def test_distribute_cards_trailing_comment() -> None:
    cards = [Card("m100", kind=Kind.MATERIAL), Card("c trailing", kind=Kind.COMMENT)]
    materials, transformations, sdef, tallies, others = sp.distribute_cards(cards)
    assert [c.text for c in materials] == ["m100"]
    assert not transformations
    assert not sdef
    assert not tallies
    assert [c.text for c in others] == ["c trailing"]
