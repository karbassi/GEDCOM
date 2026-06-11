from __future__ import annotations

import pytest

from gedcom7.lines import BannedCharacterError, Line, render, render_line


def test_simple_line() -> None:
    assert render_line(Line(0, "HEAD")) == ["0 HEAD"]


def test_line_with_value() -> None:
    assert render_line(Line(2, "VERS", "7.0")) == ["2 VERS 7.0"]


def test_line_with_xref() -> None:
    assert render_line(Line(0, "INDI", xref="@I1@")) == ["0 @I1@ INDI"]


def test_pointer_value_not_escaped() -> None:
    assert render_line(Line(1, "SUBM", "@U1@", is_pointer=True)) == ["1 SUBM @U1@"]


def test_no_trailing_space_when_no_value() -> None:
    assert render_line(Line(1, "MARR")) == ["1 MARR"]


def test_empty_value_is_same_as_no_value() -> None:
    assert render_line(Line(1, "EVEN", "")) == ["1 EVEN"]


def test_cont_splitting() -> None:
    assert render_line(Line(1, "NOTE", "line one\nline two")) == [
        "1 NOTE line one",
        "2 CONT line two",
    ]


def test_blank_line_becomes_bare_cont() -> None:
    assert render_line(Line(1, "NOTE", "a\n\nb")) == ["1 NOTE a", "2 CONT", "2 CONT b"]


def test_leading_at_is_doubled() -> None:
    assert render_line(Line(1, "NOTE", "@me handle")) == ["1 NOTE @@me handle"]


def test_internal_at_is_not_doubled() -> None:
    assert render_line(Line(1, "NOTE", "me@example.com")) == ["1 NOTE me@example.com"]


def test_leading_at_doubled_on_continuation() -> None:
    assert render_line(Line(1, "NOTE", "x\n@y")) == ["1 NOTE x", "2 CONT @@y"]


def test_crlf_and_cr_normalized_in_value() -> None:
    assert render_line(Line(1, "NOTE", "a\r\nb\rc")) == [
        "1 NOTE a",
        "2 CONT b",
        "2 CONT c",
    ]


def test_banned_character_raises() -> None:
    with pytest.raises(BannedCharacterError):
        render_line(Line(1, "NOTE", "bad\x00char"))


def test_tab_is_allowed() -> None:
    assert render_line(Line(1, "NOTE", "a\tb")) == ["1 NOTE a\tb"]


def test_render_joins_with_default_lf() -> None:
    assert render([Line(0, "HEAD"), Line(0, "TRLR")]) == "0 HEAD\n0 TRLR\n"


def test_render_with_crlf() -> None:
    assert render([Line(0, "TRLR")], eol="\r\n") == "0 TRLR\r\n"
