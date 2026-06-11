"""Branch-coverage: the "optional field absent" / alternate arcs that the
happy-path round-trips don't reach. Round-tripping minimal-but-varied models
exercises the writer's skip arcs and the reader's absent-field arcs at once;
minimal authoring documents cover the loader's, and a few direct calls cover
entry points and a parametrized helper.
"""

from __future__ import annotations

import gedcom
from gedcom import (
    ChangeDate,
    ChildLink,
    CreationDate,
    Document,
    Event,
    EventDetail,
    Family,
    Individual,
    LdsIndividualOrdinance,
    LdsOrdinanceDetail,
    NonEvent,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceDataEvent,
    read_text,
)
from gedcom.cli.loader import build_document as load
from gedcom.parse._tokenize import tokenize
from gedcom.types import Age, CalendarDate, DateExact


def _rt(doc: Document) -> None:
    text = gedcom.dumps(doc, strict=False)
    assert gedcom.dumps(read_text(text), strict=False) == text


# --- reader + writer "optional absent" arcs (round-trip minimal variants) ---


def test_non_event_without_date() -> None:
    _rt(Document(records=[Individual(xref_id="I1", non_events=[NonEvent("MARR")])]))


def test_sort_date_without_time() -> None:
    detail = EventDetail(sort_date=CalendarDate(1900))
    _rt(Document(records=[Individual(xref_id="I1", events=[Event("BIRT", detail=detail)])]))


def test_family_event_with_only_husband_age() -> None:
    detail = EventDetail(husband_age=Age(years=30))
    _rt(
        Document(
            records=[Family(xref_id="F1", events=[Event("MARR", occurred=True, detail=detail)])]
        )
    )


def test_event_famc_without_adoption() -> None:
    fam = Family(xref_id="F1")
    indi = Individual(
        xref_id="I1", events=[Event("BIRT", occurred=True, detail=EventDetail(family_child=fam))]
    )
    _rt(Document(records=[indi, fam]))


def test_ordinance_date_only_and_status_without_time() -> None:
    indi = Individual(
        xref_id="I1",
        lds_ordinances=[
            LdsIndividualOrdinance(
                "BAPL", detail=LdsOrdinanceDetail(date=CalendarDate(1990, 1, 1))
            ),
            LdsIndividualOrdinance(
                "CONL",
                detail=LdsOrdinanceDetail(
                    temple="SLAKE",
                    status=gedcom.enums.OrdinanceStatus.COMPLETED,
                    status_date=DateExact(1990, 1, 2),
                ),
            ),
        ],
    )
    _rt(Document(records=[indi]))


def test_citation_variants() -> None:
    src = Source(xref_id="S1", title="T")
    indi = Individual(
        xref_id="I1",
        source_citations=[
            SourceCitation(src, page="p1"),  # no DATA, EVEN, QUAY
            SourceCitation(src, data_date=CalendarDate(1900)),  # DATA with DATE, no TEXT
            SourceCitation(src, event="BIRT"),  # EVEN with no ROLE
        ],
    )
    _rt(Document(records=[indi, src]))


def test_source_data_event_without_date_or_place() -> None:
    src = Source(xref_id="S1", data=SourceData(events=[SourceDataEvent(["BIRT"])]))
    _rt(Document(records=[src]))


def test_metadata_without_time() -> None:
    indi = Individual(
        xref_id="I1",
        change_date=ChangeDate(DateExact(2020, 1, 1)),
        creation_date=CreationDate(DateExact(2019, 1, 1)),
    )
    _rt(Document(records=[indi]))


def test_repository_without_address() -> None:
    _rt(Document(records=[Repository(xref_id="R1", name="Archive")]))


def test_shared_note_minimal() -> None:
    _rt(Document(records=[SharedNote(xref_id="N1", text="bare")]))


def test_child_link_detail_with_non_matching_and_multiple_children() -> None:
    # Two children where only the second carries FAMC detail: the lift loop
    # iterates past the first (no-match) before finding the second.
    a = Individual(xref_id="I1")
    b = Individual(xref_id="I2")
    fam = Family(xref_id="F1", children=[a, ChildLink(b, pedigree=gedcom.enums.Pedigree.BIRTH)])
    _rt(Document(records=[a, b, fam]))


def test_header_gedc_without_version() -> None:
    # GEDC present but no VERS line -> the reader keeps the default version.
    doc = read_text("0 HEAD\n1 GEDC\n0 TRLR\n")
    assert doc.header.gedcom_version == "7.0"


def test_header_without_gedc() -> None:
    doc = read_text("0 HEAD\n0 TRLR\n")
    assert doc.header.gedcom_version == "7.0"


def test_tokenize_without_trailing_newline() -> None:
    lines = tokenize("0 HEAD\n0 TRLR")  # no final newline -> no trailing-"" to drop
    assert [line.tag for line in lines] == ["HEAD", "TRLR"]


# --- loader "optional absent" arcs (minimal authoring documents) ------------


def test_loader_minimal_variants() -> None:
    load({"individuals": [{"xref": "I1", "name": "A /B/"}]})  # no metadata
    load(
        {"families": [{"xref": "F1", "wife": "I1"}], "individuals": [{"xref": "I1"}]}
    )  # no husband
    load({"individuals": [{"xref": "I1", "non_events": [{"tag": "MARR"}]}]})  # non-event no date
    load(
        {
            "individuals": [
                {"xref": "I1", "ordinances": [{"tag": "BAPL", "detail": {"temple": "X"}}]}
            ]
        }
    )  # no family, no date
    load(
        {"sources": [{"xref": "S1", "data": {"events": [{"events": ["BIRT"]}]}}]}
    )  # data event no date/place


# --- entry point and parametrized helper -----------------------------------


def test_main_module_imports_as_module() -> None:
    # Importing (not running) gedcom.__main__ takes the `__name__ != "__main__"`
    # arc that the `python -m` runpy test does not.
    import gedcom.__main__  # noqa: F401


def test_record_props_without_xref() -> None:
    from gedcom.cli.schema import _record_props

    assert "xref" not in _record_props({"name": {"type": "string"}}, xref=False)


# --- the remaining reachable absent/alternate arcs --------------------------


def test_header_date_without_time() -> None:
    doc = read_text("0 HEAD\n1 GEDC\n2 VERS 7.0\n1 DATE 1 JAN 2024\n0 TRLR\n")
    assert doc.header.date == DateExact(2024, 1, 1) and doc.header.time is None


def test_citation_data_with_text_only() -> None:
    src = Source(xref_id="S1", title="T")
    indi = Individual(xref_id="I1", source_citations=[SourceCitation(src, data_texts=["x"])])
    _rt(Document(records=[indi, src]))


def test_header_source_without_version() -> None:
    from gedcom import Header, HeaderSource

    _rt(Document(header=Header(source=HeaderSource("App"))))


def test_sealing_without_detail() -> None:
    from gedcom import LdsSpouseSealing

    _rt(Document(records=[Family(xref_id="F1", sealings=[LdsSpouseSealing()])]))


def test_child_link_status_only_and_alias_without_phrase() -> None:
    from gedcom import Alias
    from gedcom.enums import FamcStatus

    a = Individual(xref_id="I1")
    b = Individual(xref_id="I2", aliases=[Alias(a)])  # alias with no phrase
    fam = Family(
        xref_id="F1", children=[ChildLink(a, status=FamcStatus.PROVEN)]
    )  # status, no pedigree
    _rt(Document(records=[a, b, fam]))


def test_famc_detail_for_unlisted_child() -> None:
    # I1 declares FAMC detail for F1, but F1 lists only I2 as a child: the lift
    # loop finds no match and runs to completion.
    text = (
        "0 HEAD\n1 GEDC\n2 VERS 7.0\n"
        "0 @I1@ INDI\n1 FAMC @F1@\n2 PEDI BIRTH\n"
        "0 @I2@ INDI\n"
        "0 @F1@ FAM\n1 CHIL @I2@\n0 TRLR\n"
    )
    doc = read_text(text)
    assert len(doc.records) == 3


def test_spouse_node_without_age() -> None:
    # A HUSB container with no AGE child: the detail loop skips it.
    doc = read_text("0 HEAD\n1 GEDC\n2 VERS 7.0\n0 @F1@ FAM\n1 MARR\n2 HUSB\n0 TRLR\n")
    fam = doc.records[0]
    assert isinstance(fam, Family)


def test_status_without_date() -> None:
    # A STAT with no DATE: the reader tolerates it (status set, no status_date).
    doc = read_text("0 HEAD\n1 GEDC\n2 VERS 7.0\n0 @I1@ INDI\n1 BAPL\n2 STAT COMPLETED\n0 TRLR\n")
    indi = doc.records[0]
    assert isinstance(indi, Individual)
    assert indi.lds_ordinances[0].detail is not None


def test_loader_ordinance_detail_date_without_temple() -> None:
    load(
        {
            "individuals": [
                {"xref": "I1", "ordinances": [{"tag": "BAPL", "detail": {"date": "1 JAN 1990"}}]}
            ]
        }
    )
