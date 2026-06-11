from __future__ import annotations

import pytest

from gedcom7.types import (
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
    date_value_gedcom,
    integer,
    text_list,
)

# --- Calendar dates ---


def test_gregorian_date_omits_calendar() -> None:
    assert CalendarDate(1937, 10, 2).gedcom() == "2 OCT 1937"


def test_year_only_date() -> None:
    assert CalendarDate(1937).gedcom() == "1937"


def test_month_year_date() -> None:
    assert CalendarDate(1937, 10).gedcom() == "OCT 1937"


def test_julian_date_emits_calendar() -> None:
    assert CalendarDate(1700, 3, 1, Calendar.JULIAN).gedcom() == "JULIAN 1 MAR 1700"


def test_french_republican_months() -> None:
    assert CalendarDate(8, 2, calendar=Calendar.FRENCH_R).gedcom() == "FRENCH_R BRUM 8"


def test_hebrew_months() -> None:
    assert CalendarDate(5780, 1, calendar=Calendar.HEBREW).gedcom() == "HEBREW TSH 5780"


def test_bce_epoch() -> None:
    assert CalendarDate(44, bce=True).gedcom() == "44 BCE"


def test_bce_rejected_for_hebrew() -> None:
    with pytest.raises(ValueError, match="epoch"):
        CalendarDate(100, calendar=Calendar.HEBREW, bce=True)


def test_day_without_month_rejected() -> None:
    with pytest.raises(ValueError, match="day requires a month"):
        CalendarDate(1937, None, 2)


def test_month_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="out of range"):
        CalendarDate(1937, 13)


# --- Date exact ---


def test_date_exact() -> None:
    assert DateExact(1937, 10, 2).gedcom() == "2 OCT 1937"


# --- Approximations, ranges, periods ---


def test_approx_date() -> None:
    assert ApproxDate(CalendarDate(1900), "EST").gedcom() == "EST 1900"


def test_date_range_between() -> None:
    dv = DateRange(CalendarDate(1903), CalendarDate(1904))
    assert date_value_gedcom(dv) == "BET 1903 AND 1904"


def test_date_range_after_and_before() -> None:
    assert DateRange(after=CalendarDate(1900)).gedcom() == "AFT 1900"
    assert DateRange(before=CalendarDate(1900)).gedcom() == "BEF 1900"


def test_date_period_from_to() -> None:
    dv = DatePeriod(CalendarDate(1670), CalendarDate(1800))
    assert date_value_gedcom(dv) == "FROM 1670 TO 1800"


def test_date_period_per_date_calendar() -> None:
    dv = DatePeriod(CalendarDate(1670), CalendarDate(1800, calendar=Calendar.JULIAN))
    assert dv.gedcom() == "FROM 1670 TO JULIAN 1800"


def test_empty_date_period() -> None:
    assert DatePeriod().gedcom() == ""


# --- Time ---


def test_time_hours_minutes() -> None:
    assert Time(2, 50).gedcom() == "02:50"


def test_time_full_with_utc() -> None:
    assert Time(23, 0, 5, 250, utc=True).gedcom() == "23:00:05.250Z"


def test_time_rejects_bad_hour() -> None:
    with pytest.raises(ValueError, match="hour"):
        Time(24, 0)


# --- Age ---


def test_age_full() -> None:
    assert Age(35, 11, 8, 21).gedcom() == "35y 11m 8w 21d"


def test_age_partial() -> None:
    assert Age(days=363).gedcom() == "363d"


def test_age_with_bound() -> None:
    assert Age(days=8, bound=">").gedcom() == "> 8d"


def test_age_rejects_negative() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Age(years=-1)


# --- Coordinates ---


def test_latitude_north() -> None:
    assert Latitude(18.150944).gedcom() == "N18.150944"


def test_latitude_south() -> None:
    assert Latitude(-18.15).gedcom() == "S18.15"


def test_longitude_east() -> None:
    assert Longitude(168.150944).gedcom() == "E168.150944"


def test_latitude_out_of_range() -> None:
    with pytest.raises(ValueError, match="out of range"):
        Latitude(91)


# --- Helpers ---


def test_integer() -> None:
    assert integer(0) == "0"
    with pytest.raises(ValueError, match="non-negative"):
        integer(-1)


def test_text_list() -> None:
    assert text_list(["a", "b", "c"]) == "a, b, c"
