"""INDI.FAMC membership detail (PEDI/STAT) and event-level FAMC."""

from __future__ import annotations

from gedcom import (
    ChildLink,
    Document,
    Event,
    EventDetail,
    Family,
    Individual,
    PersonalName,
    dumps,
)
from gedcom.enums import AdoptingParent, FamcStatus, Pedigree


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_childlink_emits_pedi_and_stat_on_derived_famc() -> None:
    bob = _indi()
    fam = Family(children=[ChildLink(bob, pedigree=Pedigree.ADOPTED, status=FamcStatus.PROVEN)])
    out = dumps(Document(records=[bob, fam]))
    famc = out[out.index("0 @I1@ INDI") :]
    assert "1 FAMC @F1@\n2 PEDI ADOPTED\n2 STAT PROVEN\n" in famc
    # The family still emits the CHIL back-pointer (derived integrity intact).
    assert "1 CHIL @I1@\n" in out


def test_childlink_pedigree_phrase() -> None:
    bob = _indi()
    fam = Family(children=[ChildLink(bob, pedigree=Pedigree.OTHER, pedigree_phrase="donor")])
    out = dumps(Document(records=[bob, fam]))
    assert "1 FAMC @F1@\n2 PEDI OTHER\n3 PHRASE donor\n" in out


def test_bare_individual_child_emits_plain_famc() -> None:
    bob = _indi()
    fam = Family(children=[bob])
    out = dumps(Document(records=[bob, fam]))
    indi = out[out.index("0 @I1@ INDI") :]
    assert "1 FAMC @F1@\n" in indi
    assert "PEDI" not in indi and "STAT" not in indi


def test_event_level_famc_on_adoption() -> None:
    fam = Family()
    child = _indi(
        events=[
            Event(
                "ADOP",
                detail=EventDetail(family_child=fam, adopting_parent=AdoptingParent.BOTH),
            )
        ]
    )
    out = dumps(Document(records=[child, fam]))
    assert "1 ADOP\n2 FAMC @F1@\n3 ADOP BOTH\n" in out


def test_event_level_famc_on_birth_without_adopting_parent() -> None:
    fam = Family()
    child = _indi(events=[Event("BIRT", occurred=True, detail=EventDetail(family_child=fam))])
    out = dumps(Document(records=[child, fam]))
    assert "1 BIRT Y\n2 FAMC @F1@\n" in out
