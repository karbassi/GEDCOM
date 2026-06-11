"""Event-detail AGE (individual + HUSB/WIFE) and SDATE (sort date)."""

from __future__ import annotations

from gedcom7 import (
    Document,
    Event,
    EventDetail,
    Family,
    Individual,
    PersonalName,
    dumps,
)
from gedcom7.types import Age, CalendarDate, Time


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_individual_event_age() -> None:
    indi = _indi(
        events=[
            Event("DEAT", occurred=True, detail=EventDetail(age=Age(years=72), age_phrase="abt"))
        ]
    )
    out = dumps(Document(records=[indi]))
    assert "1 DEAT Y\n2 AGE 72y\n3 PHRASE abt\n" in out


def test_sort_date_with_time_and_phrase() -> None:
    indi = _indi(
        events=[
            Event(
                "BIRT",
                detail=EventDetail(
                    sort_date=CalendarDate(1850), sort_date_time=Time(1, 2), sort_date_phrase="sp"
                ),
            )
        ]
    )
    out = dumps(Document(records=[indi]))
    assert "1 BIRT\n2 SDATE 1850\n3 TIME 01:02\n3 PHRASE sp\n" in out


def test_family_event_spouse_ages() -> None:
    husband = _indi()
    wife = _indi()
    fam = Family(
        husband=husband,
        wife=wife,
        events=[
            Event(
                "MARR",
                occurred=True,
                detail=EventDetail(husband_age=Age(years=30), wife_age=Age(years=28, bound=">")),
            )
        ],
    )
    out = dumps(Document(records=[husband, wife, fam]))
    assert "1 MARR Y\n2 HUSB\n3 AGE 30y\n2 WIFE\n3 AGE > 28y\n" in out
