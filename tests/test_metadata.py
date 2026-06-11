from __future__ import annotations

from gedcom7 import (
    ChangeDate,
    CreationDate,
    Document,
    Individual,
    Note,
    PersonalName,
    Submitter,
    dumps,
)
from gedcom7.types import DateExact, Time


def test_change_and_creation_dates_emitted_last() -> None:
    indi = Individual(
        names=[PersonalName("X //")],
        change_date=ChangeDate(DateExact(2026, 6, 10), time=Time(14, 30)),
        creation_date=CreationDate(DateExact(2020, 1, 1)),
    )
    out = dumps(Document(records=[indi]))
    assert "1 CHAN\n2 DATE 10 JUN 2026\n3 TIME 14:30\n1 CREA\n2 DATE 1 JAN 2020\n0 TRLR" in out


def test_change_date_with_note() -> None:
    subm = Submitter(
        "Ali",
        change_date=ChangeDate(DateExact(2026, 6, 10), notes=[Note("merged duplicate")]),
    )
    out = dumps(Document(records=[subm]))
    assert "1 CHAN\n2 DATE 10 JUN 2026\n2 NOTE merged duplicate\n" in out
