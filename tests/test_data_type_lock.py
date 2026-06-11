"""Lock the 16 value types' formatting to registry-sourced worked examples.

The expected payloads in ``registry/data-type-examples.tsv`` are taken from
``GEDCOM-registries/data-type/standard``. Each row names a ``builder`` mapped
here to a value-type construction; the test asserts the output matches and that
builders and fixture rows stay in lockstep.
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

from gedcom7.types import (
    Age,
    Calendar,
    CalendarDate,
    DateExact,
    DatePeriod,
    Latitude,
    Longitude,
    Time,
)

_FIXTURE = Path(__file__).resolve().parents[1] / "registry" / "data-type-examples.tsv"

# builder key -> the value-type output it should produce.
BUILDERS: dict[str, Callable[[], str]] = {
    "age_years": lambda: Age(years=35).gedcom(),
    "age_zero": lambda: Age(years=0).gedcom(),
    "age_days": lambda: Age(days=363).gedcom(),
    "age_weeks_days": lambda: Age(weeks=51, days=6).gedcom(),
    "age_bound_lt": lambda: Age(days=8, bound="<").gedcom(),
    "time_hm": lambda: Time(2, 50).gedcom(),
    "time_hms": lambda: Time(23, 59, 59).gedcom(),
    "time_utc": lambda: Time(2, 50, utc=True).gedcom(),
    "lat_north": lambda: Latitude(18.150944).gedcom(),
    "long_east": lambda: Longitude(168.150944).gedcom(),
    "date_exact": lambda: DateExact(2024, 1, 31).gedcom(),
    "date_period": lambda: DatePeriod(CalendarDate(1670), CalendarDate(1800)).gedcom(),
    "date_julian": lambda: CalendarDate(1700, 3, 1, Calendar.JULIAN).gedcom(),
    "date_french": lambda: CalendarDate(8, 2, calendar=Calendar.FRENCH_R).gedcom(),
    "date_hebrew": lambda: CalendarDate(5780, 1, calendar=Calendar.HEBREW).gedcom(),
    "date_bce": lambda: CalendarDate(44, bce=True).gedcom(),
}


def _fixture_rows() -> list[dict[str, str]]:
    with _FIXTURE.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_value_types_reproduce_registry_examples() -> None:
    for row in _fixture_rows():
        builder = BUILDERS[row["builder"]]
        assert builder() == row["gedcom"], f"{row['datatype']}/{row['builder']} drifted"


def test_builders_and_fixture_stay_in_lockstep() -> None:
    fixture_builders = {row["builder"] for row in _fixture_rows()}
    assert set(BUILDERS) == fixture_builders
