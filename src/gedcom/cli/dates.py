"""The CLI's date dialect: friendly date strings → GEDCOM value types.

This parses the *authoring document's* date fields — it is not a GEDCOM
reader. The accepted grammar mirrors the GEDCOM date payload so genealogists
can write what they already know::

    1 JAN 1900            JAN 1900            1900            100 BCE
    ABT 1850   CAL 1850   EST 1850
    BET 1900 AND 1910     AFT 1900     BEF 1910
    FROM 1920 TO 1930     FROM 1920    TO 1930
    JULIAN 1 MAR 1700     HEBREW 1 TSH 5700     FRENCH_R 1 VEND 1

Native ``date``/``datetime`` values (as YAML produces them) are accepted
wherever a date is expected.
"""

from __future__ import annotations

import datetime as _dt

from ..types import (
    _MONTHS,
    ApproxDate,
    Calendar,
    CalendarDate,
    DateExact,
    DatePeriod,
    DateRange,
    DateValue,
)
from .errors import LoadError

_CALENDARS = {c.value: c for c in Calendar}
_MONTH_INDEX: dict[Calendar, dict[str, int]] = {
    cal: {name: i + 1 for i, name in enumerate(months)} for cal, months in _MONTHS.items()
}
_APPROX = {"ABT", "CAL", "EST"}


def parse_date(value: object) -> DateValue:
    """Parse any authoring date field into a GEDCOM :data:`DateValue`."""
    if isinstance(value, _dt.datetime):
        return CalendarDate(value.year, value.month, value.day)
    if isinstance(value, _dt.date):
        return CalendarDate(value.year, value.month, value.day)
    if not isinstance(value, str):
        raise LoadError(f"expected a date string, got {type(value).__name__}")
    tokens = value.upper().split()
    if not tokens:
        raise LoadError("empty date")
    head = tokens[0]
    if head in _APPROX:
        return ApproxDate(_calendar_date(tokens[1:], value), kind=head)
    if head == "BET":
        after, before = _split(tokens[1:], "AND", value)
        return DateRange(after=_calendar_date(after, value), before=_calendar_date(before, value))
    if head == "AFT":
        return DateRange(after=_calendar_date(tokens[1:], value))
    if head == "BEF":
        return DateRange(before=_calendar_date(tokens[1:], value))
    if head == "FROM":
        start, end = _split(tokens[1:], "TO", value, optional=True)
        return DatePeriod(start=_calendar_date(start, value), end=_optional(end, value))
    if head == "TO":
        return DatePeriod(end=_calendar_date(tokens[1:], value))
    return _calendar_date(tokens, value)


def parse_date_exact(value: object) -> DateExact:
    """Parse an exact (timestamp) date: ``day MON year`` or a native date."""
    if isinstance(value, _dt.datetime):
        return DateExact(value.year, value.month, value.day)
    if isinstance(value, _dt.date):
        return DateExact(value.year, value.month, value.day)
    if not isinstance(value, str):
        raise LoadError(f"expected an exact date, got {type(value).__name__}")
    date = _calendar_date(value.upper().split(), value)
    if date.calendar is not Calendar.GREGORIAN or date.bce:
        raise LoadError(f"{value!r} must be an exact Gregorian date")
    if date.month is None or date.day is None:
        raise LoadError(f"{value!r} must be a full 'day MONTH year' date")
    return DateExact(date.year, date.month, date.day)


def _split(
    tokens: list[str], keyword: str, raw: str, *, optional: bool = False
) -> tuple[list[str], list[str]]:
    if keyword in tokens:
        index = tokens.index(keyword)
        return tokens[:index], tokens[index + 1 :]
    if optional:
        return tokens, []
    raise LoadError(f"{raw!r} is missing {keyword!r}")


def _optional(tokens: list[str], raw: str) -> CalendarDate | None:
    return _calendar_date(tokens, raw) if tokens else None


def _calendar_date(tokens: list[str], raw: str) -> CalendarDate:
    tokens = list(tokens)
    if not tokens:
        raise LoadError(f"{raw!r} is missing a date")
    calendar = Calendar.GREGORIAN
    if tokens[0] in _CALENDARS:
        calendar = _CALENDARS[tokens.pop(0)]
    bce = False
    if tokens and tokens[-1] in ("BCE", "BC"):
        bce = True
        tokens.pop()
    if not tokens:
        raise LoadError(f"{raw!r} is missing a year")
    if len(tokens) == 1:
        return CalendarDate(_year(tokens[0], raw), calendar=calendar, bce=bce)
    if len(tokens) == 2:
        month = _month(tokens[0], calendar, raw)
        return CalendarDate(_year(tokens[1], raw), month=month, calendar=calendar, bce=bce)
    if len(tokens) == 3:
        day = _int(tokens[0], raw, "day")
        month = _month(tokens[1], calendar, raw)
        return CalendarDate(_year(tokens[2], raw), month=month, day=day, calendar=calendar, bce=bce)
    raise LoadError(f"{raw!r} has too many parts for a date")


def _month(token: str, calendar: Calendar, raw: str) -> int:
    index = _MONTH_INDEX[calendar].get(token)
    if index is None:
        allowed = ", ".join(_MONTH_INDEX[calendar])
        raise LoadError(f"{token!r} in {raw!r} is not a {calendar.value} month ({allowed})")
    return index


def _year(token: str, raw: str) -> int:
    return _int(token, raw, "year")


def _int(token: str, raw: str, what: str) -> int:
    if not token.isdigit():
        raise LoadError(f"{token!r} in {raw!r} is not a valid {what}")
    return int(token)
