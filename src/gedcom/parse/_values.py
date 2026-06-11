"""GEDCOM payload strings → value objects, the inverse of :mod:`gedcom.types`.

Each parser is the read-side counterpart of a value type's ``gedcom()`` method
(or an enum/integer/list helper). Parsing is strict (ADR-0005): a payload that
does not match the form it should, or a value the target value type rejects at
construction, raises :class:`~gedcom.parse.errors.ParseError`.
"""

from __future__ import annotations

from enum import StrEnum

from ..types import (
    _MONTHS,
    Age,
    ApproxDate,
    Calendar,
    CalendarDate,
    DateExact,
    DatePeriod,
    DateRange,
    DateValue,
    Latitude,
    Longitude,
    Time,
)
from .errors import ParseError

_CALENDAR_BY_NAME = {c.value: c for c in Calendar}
_AGE_UNITS = {"y": "years", "m": "months", "w": "weeks", "d": "days"}


def _month_index(token: str, calendar: Calendar, lineno: int | None) -> int:
    """1-based month number for a month tag in the given calendar."""
    try:
        return _MONTHS[calendar].index(token) + 1
    except ValueError:
        raise ParseError(f"unknown {calendar.value} month {token!r}", line=lineno) from None


def parse_calendar_date(text: str, *, line: int | None = None) -> CalendarDate:
    """Parse a single calendar date: ``[cal] [[day] month] year [BCE]``."""
    tokens = text.split()
    if not tokens:
        raise ParseError("empty date", line=line)

    calendar = Calendar.GREGORIAN
    if tokens[0] in _CALENDAR_BY_NAME:
        calendar = _CALENDAR_BY_NAME[tokens[0]]
        tokens = tokens[1:]

    bce = False
    if tokens and tokens[-1] == "BCE":
        bce = True
        tokens = tokens[:-1]

    if not tokens:
        raise ParseError(f"date {text!r} has no year", line=line)
    try:
        year = int(tokens[-1])
    except ValueError:
        raise ParseError(f"date year {tokens[-1]!r} is not an integer", line=line) from None

    month: int | None = None
    day: int | None = None
    rest = tokens[:-1]
    if len(rest) == 1:
        month = _month_index(rest[0], calendar, line)
    elif len(rest) == 2:
        month = _month_index(rest[1], calendar, line)
        try:
            day = int(rest[0])
        except ValueError:
            raise ParseError(f"date day {rest[0]!r} is not an integer", line=line) from None
    elif rest:
        raise ParseError(f"malformed date {text!r}", line=line)

    try:
        return CalendarDate(year=year, month=month, day=day, calendar=calendar, bce=bce)
    except ValueError as exc:
        raise ParseError(str(exc), line=line) from None


def parse_date_exact(text: str, *, line: int | None = None) -> DateExact:
    """Parse a fully-known Gregorian date: ``day month year``."""
    tokens = text.split()
    if len(tokens) != 3:
        raise ParseError(f"exact date {text!r} must be 'day month year'", line=line)
    day_s, month_tag, year_s = tokens
    try:
        return DateExact(
            year=int(year_s),
            month=_month_index(month_tag, Calendar.GREGORIAN, line),
            day=int(day_s),
        )
    except ValueError as exc:
        raise ParseError(str(exc), line=line) from None


def parse_date_value(text: str, *, line: int | None = None) -> DateValue:
    """Parse any date payload: approximations, ranges, periods, or a plain date."""
    for kind in ("ABT", "CAL", "EST"):
        prefix = f"{kind} "
        if text.startswith(prefix):
            return ApproxDate(parse_calendar_date(text[len(prefix) :], line=line), kind)
    if text.startswith("BET "):
        after, _, before = text[4:].partition(" AND ")
        if not before:
            raise ParseError(f"range {text!r} missing 'AND'", line=line)
        return DateRange(
            after=parse_calendar_date(after, line=line),
            before=parse_calendar_date(before, line=line),
        )
    if text.startswith("AFT "):
        return DateRange(after=parse_calendar_date(text[4:], line=line))
    if text.startswith("BEF "):
        return DateRange(before=parse_calendar_date(text[4:], line=line))
    if text.startswith("FROM ") or text.startswith("TO "):
        return parse_date_period(text, line=line)
    return parse_calendar_date(text, line=line)


def parse_date_period(text: str, *, line: int | None = None) -> DatePeriod:
    """Parse a period payload: ``FROM a [TO b]``, ``TO b``, or empty."""
    if text == "":
        return DatePeriod()
    if text.startswith("FROM "):
        start, sep, end = text[5:].partition(" TO ")
        return DatePeriod(
            start=parse_calendar_date(start, line=line),
            end=parse_calendar_date(end, line=line) if sep else None,
        )
    if text.startswith("TO "):
        return DatePeriod(end=parse_calendar_date(text[3:], line=line))
    raise ParseError(f"malformed date period {text!r}", line=line)


def parse_time(text: str, *, line: int | None = None) -> Time:
    """Parse a time payload: ``hh:mm[:ss[.fff]][Z]``."""
    utc = text.endswith("Z")
    body = text[:-1] if utc else text
    parts = body.split(":")
    if len(parts) not in (2, 3):
        raise ParseError(f"malformed time {text!r}", line=line)
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second: int | None = None
        fraction: int | None = None
        if len(parts) == 3:
            sec_s, dot, frac_s = parts[2].partition(".")
            second = int(sec_s)
            fraction = int(frac_s) if dot else None
        return Time(hour=hour, minute=minute, second=second, fraction=fraction, utc=utc)
    except ValueError as exc:
        raise ParseError(str(exc) if str(exc) else f"malformed time {text!r}", line=line) from None


def parse_age(text: str, *, line: int | None = None) -> Age:
    """Parse an age payload: ``[< | >] <count><unit>...``."""
    tokens = text.split()
    bound: str | None = None
    if tokens and tokens[0] in ("<", ">"):
        bound = tokens[0]
        tokens = tokens[1:]
    fields: dict[str, int] = {}
    for token in tokens:
        unit = token[-1:]
        if unit not in _AGE_UNITS:
            raise ParseError(f"unknown age unit in {token!r}", line=line)
        try:
            fields[_AGE_UNITS[unit]] = int(token[:-1])
        except ValueError:
            raise ParseError(f"malformed age component {token!r}", line=line) from None
    try:
        return Age(bound=bound, **fields)
    except ValueError as exc:
        raise ParseError(str(exc), line=line) from None


def _parse_degrees(text: str, positive: str, negative: str, line: int | None) -> float:
    if not text or text[0] not in (positive, negative):
        raise ParseError(f"coordinate {text!r} missing hemisphere", line=line)
    sign = 1.0 if text[0] == positive else -1.0
    try:
        return sign * float(text[1:])
    except ValueError:
        raise ParseError(f"malformed coordinate {text!r}", line=line) from None


def parse_latitude(text: str, *, line: int | None = None) -> Latitude:
    try:
        return Latitude(_parse_degrees(text, "N", "S", line))
    except ValueError as exc:
        raise ParseError(str(exc), line=line) from None


def parse_longitude(text: str, *, line: int | None = None) -> Longitude:
    try:
        return Longitude(_parse_degrees(text, "E", "W", line))
    except ValueError as exc:
        raise ParseError(str(exc), line=line) from None


def parse_integer(text: str, *, line: int | None = None) -> int:
    try:
        value = int(text)
    except ValueError:
        raise ParseError(f"{text!r} is not an integer", line=line) from None
    if value < 0:
        raise ParseError(f"integer {value} must be non-negative", line=line)
    return value


def parse_text_list(text: str) -> list[str]:
    """Split a List:Text / List:Enum payload on the ``, `` separator."""
    return text.split(", ") if text else []


def parse_enum[E: StrEnum](text: str, enum_cls: type[E]) -> E | str:
    """Resolve a payload to an enum member, or keep a ``_``-prefixed extension."""
    try:
        return enum_cls(text)
    except ValueError:
        if text.startswith("_"):
            return text
        raise ParseError(f"{text!r} is not a valid {enum_cls.__name__} value") from None


def parse_enum_list[E: StrEnum](text: str, enum_cls: type[E]) -> list[E | str]:
    """Parse a List:Enum payload into members / extension strings."""
    return [parse_enum(item, enum_cls) for item in parse_text_list(text)]
