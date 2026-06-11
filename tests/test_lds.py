from __future__ import annotations

import pytest

from gedcom7 import (
    Document,
    Family,
    Individual,
    LdsIndividualOrdinance,
    LdsOrdinanceDetail,
    LdsSpouseSealing,
    PersonalName,
    ValidationError,
    dumps,
)
from gedcom7.enums import OrdinanceStatus
from gedcom7.types import CalendarDate, DateExact


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_endowment_with_temple_and_status() -> None:
    detail = LdsOrdinanceDetail(
        date=CalendarDate(1840, 5, 1),
        temple=" SLAKE",
        status=OrdinanceStatus.COMPLETED,
        status_date=DateExact(1840, 5, 2),
    )
    indi = _indi(lds_ordinances=[LdsIndividualOrdinance("ENDL", detail=detail)])
    out = dumps(Document(records=[indi]))
    assert "1 ENDL\n2 DATE 1 MAY 1840\n2 TEMP  SLAKE\n2 STAT COMPLETED\n3 DATE 2 MAY 1840\n" in out


def test_slgc_requires_famc() -> None:
    parents = Family()
    child = _indi(lds_ordinances=[LdsIndividualOrdinance("SLGC", family=parents)])
    out = dumps(Document(records=[child, parents]))
    assert "1 SLGC\n2 FAMC @F1@\n" in out


def test_slgc_without_famc_raises() -> None:
    child = _indi(lds_ordinances=[LdsIndividualOrdinance("SLGC")])
    with pytest.raises(ValidationError, match="SLGC requires a FAMC"):
        dumps(Document(records=[child]))


def test_status_without_date_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="STAT requires a DATE"):
        LdsOrdinanceDetail(status=OrdinanceStatus.COMPLETED)


def test_spouse_sealing_on_family() -> None:
    detail = LdsOrdinanceDetail(date=CalendarDate(1900, 6, 1), temple="LOGAN")
    fam = Family(sealings=[LdsSpouseSealing(detail=detail)])
    out = dumps(Document(records=[fam]))
    assert "0 @F1@ FAM\n1 SLGS\n2 DATE 1 JUN 1900\n2 TEMP LOGAN\n" in out
