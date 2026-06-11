"""The CLI date dialect: friendly strings/native dates → GEDCOM value types."""

from __future__ import annotations

import datetime

import pytest

from gedcom.cli.dates import parse_date, parse_date_exact
from gedcom.cli.errors import LoadError


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1 JAN 1900", "1 JAN 1900"),
        ("JAN 1900", "JAN 1900"),
        ("1900", "1900"),
        ("100 BCE", "100 BCE"),
        ("abt 1850", "ABT 1850"),
        ("CAL 1850", "CAL 1850"),
        ("est 1 feb 1850", "EST 1 FEB 1850"),
        ("BET 1900 AND 1910", "BET 1900 AND 1910"),
        ("AFT 1900", "AFT 1900"),
        ("BEF 1910", "BEF 1910"),
        ("FROM 1920 TO 1930", "FROM 1920 TO 1930"),
        ("FROM 1920", "FROM 1920"),
        ("TO 1930", "TO 1930"),
        ("JULIAN 1 MAR 1700", "JULIAN 1 MAR 1700"),
        ("HEBREW 1 TSH 5700", "HEBREW 1 TSH 5700"),
        ("FRENCH_R 1 VEND 1", "FRENCH_R 1 VEND 1"),
    ],
)
def test_parse_date_roundtrips_to_gedcom(text: str, expected: str) -> None:
    assert parse_date(text).gedcom() == expected


def test_parse_date_accepts_native_date() -> None:
    assert parse_date(datetime.date(1850, 6, 1)).gedcom() == "1 JUN 1850"


def test_parse_date_exact_native_and_string() -> None:
    assert parse_date_exact("2 FEB 2024").gedcom() == "2 FEB 2024"
    assert parse_date_exact(datetime.datetime(2024, 2, 2, 9, 0)).gedcom() == "2 FEB 2024"


@pytest.mark.parametrize(
    "text",
    ["Jannuary 1900", "BET 1900", "1 13 1900", "", "FROM", "abt"],
)
def test_parse_date_rejects_malformed(text: str) -> None:
    with pytest.raises(LoadError):
        parse_date(text)


def test_parse_date_exact_requires_full_gregorian() -> None:
    with pytest.raises(LoadError):
        parse_date_exact("1900")
    with pytest.raises(LoadError):
        parse_date_exact("JULIAN 1 MAR 1700")
