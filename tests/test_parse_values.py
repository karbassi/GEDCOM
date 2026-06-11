"""Value-layer round-trip: ``parse(render(v)) == v`` (PRD: gedcom-reader, slice 02)."""

from __future__ import annotations

import pytest

from gedcom.enums import NameType, Quality, Restriction, Role
from gedcom.parse import _values as v
from gedcom.parse.errors import ParseError
from gedcom.types import (
    Age,
    ApproxDate,
    Calendar,
    CalendarDate,
    DateExact,
    DatePeriod,
    DateRange,
    Latitude,
    Longitude,
    Time,
)

CALENDAR_DATES = [
    CalendarDate(1937, 10, 2),
    CalendarDate(1937),
    CalendarDate(1937, 10),
    CalendarDate(1700, 3, 1, Calendar.JULIAN),
    CalendarDate(8, 2, calendar=Calendar.FRENCH_R),
    CalendarDate(5780, 1, calendar=Calendar.HEBREW),
    CalendarDate(44, bce=True),
]

DATE_VALUES = [
    *CALENDAR_DATES,
    ApproxDate(CalendarDate(1900), "ABT"),
    ApproxDate(CalendarDate(1900, 6), "CAL"),
    ApproxDate(CalendarDate(1900, 6, 1), "EST"),
    DateRange(after=CalendarDate(1900), before=CalendarDate(1910)),
    DateRange(after=CalendarDate(1900)),
    DateRange(before=CalendarDate(1910)),
    DatePeriod(CalendarDate(1670), CalendarDate(1800)),
    DatePeriod(start=CalendarDate(1670)),
    DatePeriod(end=CalendarDate(1800)),
]

TIMES = [Time(2, 50), Time(23, 59, 59), Time(2, 50, utc=True), Time(8, 5, 3, 250, utc=True)]
AGES = [Age(years=35), Age(years=0), Age(days=363), Age(weeks=51, days=6), Age(days=8, bound="<")]
LATITUDES = [Latitude(18.150944), Latitude(-33.0), Latitude(0.0)]
LONGITUDES = [Longitude(168.150944), Longitude(-122.5), Longitude(0.0)]


@pytest.mark.parametrize("date", DATE_VALUES, ids=lambda d: d.gedcom())
def test_date_value_roundtrips(date: object) -> None:
    assert v.parse_date_value(date.gedcom()) == date  # type: ignore[attr-defined]


@pytest.mark.parametrize("date", [DateExact(2024, 1, 31), DateExact(1937, 10, 2)])
def test_date_exact_roundtrips(date: DateExact) -> None:
    assert v.parse_date_exact(date.gedcom()) == date


@pytest.mark.parametrize("time", TIMES, ids=lambda t: t.gedcom())
def test_time_roundtrips(time: Time) -> None:
    assert v.parse_time(time.gedcom()) == time


@pytest.mark.parametrize("age", AGES, ids=lambda a: a.gedcom())
def test_age_roundtrips(age: Age) -> None:
    assert v.parse_age(age.gedcom()) == age


@pytest.mark.parametrize("lat", LATITUDES, ids=lambda x: x.gedcom())
def test_latitude_roundtrips(lat: Latitude) -> None:
    assert v.parse_latitude(lat.gedcom()) == lat


@pytest.mark.parametrize("long", LONGITUDES, ids=lambda x: x.gedcom())
def test_longitude_roundtrips(long: Longitude) -> None:
    assert v.parse_longitude(long.gedcom()) == long


def test_integer_roundtrips() -> None:
    assert v.parse_integer("0") == 0
    assert v.parse_integer("42") == 42


def test_text_list_roundtrips() -> None:
    assert v.parse_text_list("a, b, c") == ["a", "b", "c"]
    assert v.parse_text_list("") == []


@pytest.mark.parametrize(
    ("value", "enum_cls"),
    [
        (NameType.BIRTH, NameType),
        (Quality.DIRECT, Quality),
        (Role.WITNESS, Role),
        (Restriction.LOCKED, Restriction),
    ],
)
def test_enum_roundtrips(value: object, enum_cls: type) -> None:
    assert v.parse_enum(str(value), enum_cls) == value


def test_enum_keeps_extension_value() -> None:
    assert v.parse_enum("_CUSTOM", Role) == "_CUSTOM"


def test_enum_list_roundtrips() -> None:
    assert v.parse_enum_list("LOCKED, CONFIDENTIAL", Restriction) == [
        Restriction.LOCKED,
        Restriction.CONFIDENTIAL,
    ]


def test_invalid_latitude_raises() -> None:
    with pytest.raises(ParseError):
        v.parse_latitude("N91")


def test_negative_integer_raises() -> None:
    with pytest.raises(ParseError):
        v.parse_integer("-1")


def test_unknown_enum_raises() -> None:
    with pytest.raises(ParseError):
        v.parse_enum("NOPE", NameType)
