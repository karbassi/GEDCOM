from __future__ import annotations

import pytest

from gedcom7 import (
    Attribute,
    Document,
    Event,
    EventDetail,
    Family,
    Individual,
    NonEvent,
    PersonalName,
    ValidationError,
    dumps,
)
from gedcom7.types import CalendarDate, DatePeriod


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_event_with_date_asserts_occurrence() -> None:
    indi = _indi(events=[Event("DEAT", detail=EventDetail(date=CalendarDate(1937, 10, 2)))])
    out = dumps(Document(records=[indi]))
    assert "1 DEAT\n2 DATE 2 OCT 1937\n" in out


def test_event_y_payload() -> None:
    indi = _indi(events=[Event("DEAT", occurred=True)])
    assert "1 DEAT Y\n" in dumps(Document(records=[indi]))


def test_inconclusive_event_has_no_payload() -> None:
    indi = _indi(events=[Event("DEAT")])
    out = dumps(Document(records=[indi]))
    assert "1 DEAT\n" in out
    assert "1 DEAT Y" not in out


def test_attribute_presence() -> None:
    indi = _indi(attributes=[Attribute("OCCU", "Carpenter")])
    assert "1 OCCU Carpenter\n" in dumps(Document(records=[indi]))


def test_generic_even_requires_type_and_text() -> None:
    indi = _indi(events=[Event("EVEN", text="Knighted", type="Honor")])
    out = dumps(Document(records=[indi]))
    assert "1 EVEN Knighted\n2 TYPE Honor\n" in out


def test_generic_even_without_type_raises() -> None:
    indi = _indi(events=[Event("EVEN", text="Knighted")])
    with pytest.raises(ValidationError, match="EVEN requires a TYPE"):
        dumps(Document(records=[indi]))


def test_idno_requires_type() -> None:
    indi = _indi(attributes=[Attribute("IDNO", "12345")])
    with pytest.raises(ValidationError, match="IDNO requires a TYPE"):
        dumps(Document(records=[indi]))


def test_family_marriage_event() -> None:
    fam = Family(events=[Event("MARR", detail=EventDetail(date=CalendarDate(1900, 6, 1)))])
    out = dumps(Document(records=[fam]))
    assert "0 @F1@ FAM\n1 MARR\n2 DATE 1 JUN 1900\n" in out


def test_non_event() -> None:
    indi = _indi(non_events=[NonEvent("MARR", date=DatePeriod(end=CalendarDate(1880, 3, 24)))])
    out = dumps(Document(records=[indi]))
    assert "1 NO MARR\n2 DATE TO 24 MAR 1880\n" in out
