"""GEDCOM 7 data-type value objects and serializers (§2, §6).

Structured payloads (dates across the four calendars, times, ages, and
coordinates) are modelled as frozen value types that validate at
construction and render themselves to their GEDCOM string form. Plain-text
types (Text, Special, Language, MediaType, FilePath, URI) are ordinary
strings and need no class here; ``integer`` and ``text_list`` are small
formatting helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# --- Calendars (§6) ---------------------------------------------------------


class Calendar(StrEnum):
    GREGORIAN = "GREGORIAN"
    JULIAN = "JULIAN"
    FRENCH_R = "FRENCH_R"
    HEBREW = "HEBREW"


_GREGORIAN_MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]  # fmt: skip
_FRENCH_MONTHS = [
    "VEND", "BRUM", "FRIM", "NIVO", "PLUV", "VENT",
    "GERM", "FLOR", "PRAI", "MESS", "THER", "FRUC", "COMP",
]  # fmt: skip
_HEBREW_MONTHS = [
    "TSH", "CSH", "KSL", "TVT", "SHV", "ADR", "ADS",
    "NSN", "IYR", "SVN", "TMZ", "AAV", "ELL",
]  # fmt: skip

_MONTHS: dict[Calendar, list[str]] = {
    Calendar.GREGORIAN: _GREGORIAN_MONTHS,
    Calendar.JULIAN: _GREGORIAN_MONTHS,
    Calendar.FRENCH_R: _FRENCH_MONTHS,
    Calendar.HEBREW: _HEBREW_MONTHS,
}

# Calendars that permit the BCE epoch marker.
_EPOCH_CALENDARS = {Calendar.GREGORIAN, Calendar.JULIAN}


# --- Calendar dates ---------------------------------------------------------


@dataclass(frozen=True)
class CalendarDate:
    """A single date in a known calendar. ``month`` is 1-based.

    Gregorian is the default and its calendar tag is omitted on output.
    """

    year: int
    month: int | None = None
    day: int | None = None
    calendar: Calendar = Calendar.GREGORIAN
    bce: bool = False

    def __post_init__(self) -> None:
        if self.day is not None and self.month is None:
            raise ValueError("a day requires a month")
        if self.month is not None:
            months = _MONTHS[self.calendar]
            if not 1 <= self.month <= len(months):
                raise ValueError(f"month {self.month} is out of range for {self.calendar.value}")
        if self.day is not None and not 1 <= self.day <= 36:
            raise ValueError(f"day {self.day} is out of range")
        if self.bce and self.calendar not in _EPOCH_CALENDARS:
            raise ValueError(f"{self.calendar.value} does not permit an epoch")

    def gedcom(self) -> str:
        tokens: list[str] = []
        if self.calendar is not Calendar.GREGORIAN:
            tokens.append(self.calendar.value)
        if self.month is not None:
            if self.day is not None:
                tokens.append(str(self.day))
            tokens.append(_MONTHS[self.calendar][self.month - 1])
        tokens.append(str(self.year))
        if self.bce:
            tokens.append("BCE")
        return " ".join(tokens)


@dataclass(frozen=True)
class DateExact:
    """A fully-known Gregorian date (`day month year`), used for timestamps."""

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"month {self.month} is out of range")
        if not 1 <= self.day <= 31:
            raise ValueError(f"day {self.day} is out of range")

    def gedcom(self) -> str:
        return f"{self.day} {_GREGORIAN_MONTHS[self.month - 1]} {self.year}"


@dataclass(frozen=True)
class ApproxDate:
    """An approximated date: `ABT`, `CAL`, or `EST` before a date."""

    date: CalendarDate
    kind: str = "ABT"

    def __post_init__(self) -> None:
        if self.kind not in ("ABT", "CAL", "EST"):
            raise ValueError(f"unknown approximation {self.kind!r}")

    def gedcom(self) -> str:
        return f"{self.kind} {self.date.gedcom()}"


@dataclass(frozen=True)
class DateRange:
    """An imprecise range: `BET a AND b`, `AFT a`, or `BEF b`."""

    after: CalendarDate | None = None
    before: CalendarDate | None = None

    def __post_init__(self) -> None:
        if self.after is None and self.before is None:
            raise ValueError("a date range needs at least one bound")

    def gedcom(self) -> str:
        if self.after is not None and self.before is not None:
            return f"BET {self.after.gedcom()} AND {self.before.gedcom()}"
        if self.after is not None:
            return f"AFT {self.after.gedcom()}"
        assert self.before is not None
        return f"BEF {self.before.gedcom()}"


@dataclass(frozen=True)
class DatePeriod:
    """A span of days: `FROM a [TO b]` or `TO b`. May be empty."""

    start: CalendarDate | None = None
    end: CalendarDate | None = None

    def gedcom(self) -> str:
        if self.start is not None and self.end is not None:
            return f"FROM {self.start.gedcom()} TO {self.end.gedcom()}"
        if self.start is not None:
            return f"FROM {self.start.gedcom()}"
        if self.end is not None:
            return f"TO {self.end.gedcom()}"
        return ""


DateValue = CalendarDate | ApproxDate | DateRange | DatePeriod


def date_value_gedcom(value: DateValue) -> str:
    """Render any DateValue variant to its GEDCOM string."""
    return value.gedcom()


# --- Time -------------------------------------------------------------------


@dataclass(frozen=True)
class Time:
    """A 24-hour time, optionally in UTC (`Z`)."""

    hour: int
    minute: int
    second: int | None = None
    fraction: int | None = None
    utc: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.hour <= 23:
            raise ValueError(f"hour {self.hour} is out of range")
        if not 0 <= self.minute <= 59:
            raise ValueError(f"minute {self.minute} is out of range")
        if self.second is not None and not 0 <= self.second <= 59:
            raise ValueError(f"second {self.second} is out of range")
        if self.fraction is not None and self.second is None:
            raise ValueError("a fractional second requires a second")

    def gedcom(self) -> str:
        out = f"{self.hour:02d}:{self.minute:02d}"
        if self.second is not None:
            out += f":{self.second:02d}"
            if self.fraction is not None:
                out += f".{self.fraction}"
        if self.utc:
            out += "Z"
        return out


# --- Age --------------------------------------------------------------------


@dataclass(frozen=True)
class Age:
    """An age as a count of years/months/weeks/days, optionally bounded."""

    years: int | None = None
    months: int | None = None
    weeks: int | None = None
    days: int | None = None
    bound: str | None = None

    def __post_init__(self) -> None:
        for name, val in (
            ("years", self.years),
            ("months", self.months),
            ("weeks", self.weeks),
            ("days", self.days),
        ):
            if val is not None and val < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.bound not in (None, "<", ">"):
            raise ValueError(f"unknown age bound {self.bound!r}")

    def gedcom(self) -> str:
        parts = [
            f"{v}{s}"
            for v, s in (
                (self.years, "y"),
                (self.months, "m"),
                (self.weeks, "w"),
                (self.days, "d"),
            )
            if v is not None
        ]
        duration = " ".join(parts)
        if self.bound is not None:
            return f"{self.bound} {duration}".strip()
        return duration


# --- Coordinates ------------------------------------------------------------


def _format_degrees(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


@dataclass(frozen=True)
class Latitude:
    """A latitude; positive is north, negative is south."""

    value: float

    def __post_init__(self) -> None:
        if not -90 <= self.value <= 90:
            raise ValueError(f"latitude {self.value} is out of range")

    def gedcom(self) -> str:
        hemisphere = "N" if self.value >= 0 else "S"
        return f"{hemisphere}{_format_degrees(abs(self.value))}"


@dataclass(frozen=True)
class Longitude:
    """A longitude; positive is east, negative is west."""

    value: float

    def __post_init__(self) -> None:
        if not -180 <= self.value <= 180:
            raise ValueError(f"longitude {self.value} is out of range")

    def gedcom(self) -> str:
        hemisphere = "E" if self.value >= 0 else "W"
        return f"{hemisphere}{_format_degrees(abs(self.value))}"


# --- Simple helpers ---------------------------------------------------------


def integer(value: int) -> str:
    """Render a non-negative integer payload (negatives are unsupported)."""
    if value < 0:
        raise ValueError("GEDCOM integers must be non-negative")
    return str(value)


def text_list(items: list[str]) -> str:
    """Join a List:Text / List:Enum payload with the recommended `, `."""
    return ", ".join(items)
