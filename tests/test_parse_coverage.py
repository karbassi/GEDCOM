"""Error-path and edge-case coverage for the reader (PRD: gedcom-reader).

Exercises the strict failure branches (malformed grammar, missing required
values, unresolvable / mistyped pointers, undeclared extensions, bad archives)
and the less-trodden feature branches (sort dates, spouse ages, empty periods)
so the reader's behavior is pinned end to end.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

import gedcom
from gedcom import (
    Document,
    Event,
    EventDetail,
    Family,
    File,
    Individual,
    Multimedia,
    NonEvent,
    PersonalName,
    read_path,
    read_text,
)
from gedcom.parse import ParseError
from gedcom.parse._tokenize import tokenize
from gedcom.parse._tree import build_tree
from gedcom.parse._values import (
    parse_age,
    parse_calendar_date,
    parse_date_exact,
    parse_date_period,
    parse_date_value,
    parse_integer,
    parse_latitude,
    parse_longitude,
    parse_time,
)
from gedcom.types import Age, CalendarDate, DatePeriod, Time
from test_parse_roundtrip import assert_roundtrips

HEAD = "0 HEAD\n1 GEDC\n2 VERS 7.0\n"
TRLR = "0 TRLR\n"


def _doc(body: str) -> str:
    return HEAD + body + TRLR


# --- value-parser error branches --------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "",  # empty date
        "BCE",  # no year after stripping epoch
        "FOO 1900",  # bad month token (after a non-calendar leading token)
        "1 FOO 1900",  # bad month with a day
        "x JAN 1900",  # non-integer day
        "JAN xyz",  # non-integer year
        "1 2 3 4",  # too many tokens
    ],
)
def test_parse_calendar_date_rejects(bad: str) -> None:
    with pytest.raises(ParseError):
        parse_calendar_date(bad)


def test_parse_calendar_date_rejects_out_of_range_month() -> None:
    with pytest.raises(ParseError):
        parse_calendar_date("ZZZ 1900")


def test_parse_date_exact_rejects() -> None:
    with pytest.raises(ParseError):
        parse_date_exact("1900")  # wrong token count
    with pytest.raises(ParseError):
        parse_date_exact("99 JAN 1900")  # day out of range


def test_parse_date_value_rejects_range_without_and() -> None:
    with pytest.raises(ParseError, match="AND"):
        parse_date_value("BET 1900")


def test_parse_date_period_empty_and_malformed() -> None:
    assert parse_date_period("") == DatePeriod()
    with pytest.raises(ParseError):
        parse_date_period("SINCE 1900")


def test_parse_time_rejects() -> None:
    with pytest.raises(ParseError):
        parse_time("12")  # too few parts
    with pytest.raises(ParseError):
        parse_time("99:99")  # out of range


def test_parse_age_rejects() -> None:
    with pytest.raises(ParseError, match="unit"):
        parse_age("5x")
    with pytest.raises(ParseError):
        parse_age("xy")


def test_parse_coordinate_rejects() -> None:
    with pytest.raises(ParseError, match="hemisphere"):
        parse_latitude("18.0")  # missing N/S
    with pytest.raises(ParseError):
        parse_latitude("Nabc")  # non-numeric
    with pytest.raises(ParseError):
        parse_longitude("E999")  # out of range


def test_parse_integer_rejects() -> None:
    with pytest.raises(ParseError):
        parse_integer("nope")
    with pytest.raises(ParseError):
        parse_integer("-3")


# --- tokenizer / tree error branches ----------------------------------------


def test_tokenize_rejects_malformed_line() -> None:
    with pytest.raises(ParseError, match="not a GEDCOM line"):
        tokenize("nonsense\n")


def test_tokenize_rejects_leading_cont() -> None:
    with pytest.raises(ParseError, match="CONT"):
        tokenize("1 CONT orphaned\n")


def test_tree_rejects_non_zero_first_line() -> None:
    with pytest.raises(ParseError, match="level 0"):
        build_tree(tokenize("1 FOO bar\n"))


def test_tree_rejects_level_skip() -> None:
    with pytest.raises(ParseError, match="skips a level"):
        build_tree(tokenize("0 HEAD\n2 VERS 7.0\n"))


# --- document-structure error branches --------------------------------------


def test_missing_head_raises() -> None:
    with pytest.raises(ParseError, match="no HEAD"):
        read_text("0 @I1@ INDI\n0 TRLR\n")


def test_missing_trailer_raises() -> None:
    with pytest.raises(ParseError, match="no TRLR"):
        read_text(HEAD)


def test_duplicate_head_raises() -> None:
    with pytest.raises(ParseError, match="more than one HEAD"):
        read_text(HEAD + HEAD + TRLR)


def test_record_without_xref_raises() -> None:
    with pytest.raises(ParseError, match="cross-reference id"):
        read_text(_doc("0 INDI\n"))


# --- pointer resolution error branches --------------------------------------


def test_dangling_pointer_raises() -> None:
    with pytest.raises(ParseError, match="does not resolve"):
        read_text(_doc("0 @I1@ INDI\n1 ASSO @I9@\n2 ROLE FRIEND\n"))


def test_pointer_type_mismatch_raises() -> None:
    body = "0 @S1@ SOUR\n0 @I1@ INDI\n1 ASSO @S1@\n2 ROLE FRIEND\n"
    with pytest.raises(ParseError, match="expected Individual"):
        read_text(_doc(body))


def test_duplicate_xref_raises() -> None:
    with pytest.raises(ParseError, match="duplicate"):
        read_text(_doc("0 @I1@ INDI\n0 @I1@ INDI\n"))


# --- required-value error branches ------------------------------------------


def test_association_without_role_raises() -> None:
    with pytest.raises(ParseError, match="ROLE"):
        read_text(_doc("0 @I2@ INDI\n0 @I1@ INDI\n1 ASSO @I2@\n"))


def test_snote_pointer_without_value_raises() -> None:
    with pytest.raises(ParseError, match="SNOTE"):
        read_text(_doc("0 @I1@ INDI\n1 SNOTE\n"))


def test_name_translation_without_language_raises() -> None:
    with pytest.raises(ParseError, match="LANG"):
        read_text(_doc("0 @I1@ INDI\n1 NAME A /B/\n2 TRAN C /D/\n"))


def test_file_translation_without_form_raises() -> None:
    body = "0 @O1@ OBJE\n1 FILE a.jpg\n2 FORM image/jpeg\n2 TRAN b.png\n"
    with pytest.raises(ParseError, match="FORM"):
        read_text(_doc(body))


def test_change_date_without_date_raises() -> None:
    with pytest.raises(ParseError, match="CHAN"):
        read_text(_doc("0 @I1@ INDI\n1 CHAN\n"))


def test_creation_date_without_date_raises() -> None:
    with pytest.raises(ParseError, match="CREA"):
        read_text(_doc("0 @I1@ INDI\n1 CREA\n"))


def test_undeclared_extension_raises() -> None:
    with pytest.raises(ParseError, match="SCHMA"):
        read_text(_doc("0 @I1@ INDI\n1 _NOPE value\n"))


# --- GEDZIP error branch -----------------------------------------------------


def test_read_path_rejects_non_zip_gdz(tmp_path: Path) -> None:
    bad = tmp_path / "broken.gdz"
    bad.write_bytes(b"this is not a zip archive")
    with pytest.raises(ParseError, match="not a valid GEDZIP"):
        read_path(bad)


# --- under-exercised feature branches (round-trips) -------------------------


def test_sort_date_roundtrips() -> None:
    person = Individual(
        xref_id="I1",
        events=[
            Event(
                "BIRT",
                detail=EventDetail(
                    date=CalendarDate(1900, 1, 1),
                    date_time=Time(8, 30),
                    sort_date=CalendarDate(1900, 1, 2),
                    sort_date_time=Time(9, 0),
                    sort_date_phrase="best guess",
                ),
            )
        ],
    )
    assert_roundtrips(Document(records=[person]))


def test_spouse_ages_in_family_event_roundtrip() -> None:
    fam = Family(
        xref_id="F1",
        events=[
            Event(
                "MARR",
                occurred=True,
                detail=EventDetail(
                    husband_age=Age(years=30),
                    husband_age_phrase="about thirty",
                    wife_age=Age(years=28),
                ),
            )
        ],
    )
    assert_roundtrips(Document(records=[fam]))


def test_empty_non_event_period_roundtrips() -> None:
    person = Individual(xref_id="I1", non_events=[NonEvent("MARR", date=DatePeriod())])
    assert_roundtrips(Document(records=[person]))


def test_submitter_with_address_roundtrips() -> None:
    from gedcom import Address, Submitter

    subm = Submitter(xref_id="U1", name="Sub", address=Address("1 Main", city="Town"))
    assert_roundtrips(Document(records=[subm]))


def test_media_without_form_medium_roundtrips() -> None:
    media = Multimedia(xref_id="O1", files=[File("x.png", "image/png")])
    assert_roundtrips(Document(records=[media]))


def test_read_path_handles_gdz_via_zipfile(tmp_path: Path) -> None:
    # A valid zip with the member but read through read_path's .gdz branch.
    out = tmp_path / "t.gdz"
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("gedcom.ged", gedcom.dumps(Document()).encode("utf-8"))
    assert read_path(out).records == []


def test_individual_name_pieces_on_translation_roundtrip() -> None:
    person = Individual(xref_id="I1", names=[PersonalName("A /B/")])
    assert_roundtrips(Document(records=[person]))


def test_registered_extension_uses_registry_uri() -> None:
    from gedcom import ExtensionStructure

    # _AGER is a registered extension tag: its URI comes from the registry
    # (uri=None), exercising the registered-extension branch of the decoder.
    person = Individual(xref_id="I1", extensions=[ExtensionStructure("_AGER", value="30")])
    assert_roundtrips(Document(records=[person]))


def test_ordinance_detail_with_time_and_place_roundtrips() -> None:
    from gedcom import LdsIndividualOrdinance, LdsOrdinanceDetail, Place

    person = Individual(
        xref_id="I1",
        lds_ordinances=[
            LdsIndividualOrdinance(
                "BAPL",
                detail=LdsOrdinanceDetail(
                    date=CalendarDate(1990, 1, 1),
                    date_time=Time(10, 30),
                    date_phrase="morning",
                    place=Place(["Temple Square", "UT"]),
                ),
            )
        ],
    )
    assert_roundtrips(Document(records=[person]))


def test_calendar_date_construction_error_propagates() -> None:
    # Tokens parse, but HEBREW + BCE is rejected by CalendarDate's invariants.
    with pytest.raises(ParseError, match="epoch"):
        parse_calendar_date("HEBREW TSH 5780 BCE")


def test_age_construction_error_propagates() -> None:
    with pytest.raises(ParseError, match="non-negative"):
        parse_age("-5y")


def test_tokenize_rejects_missing_tag() -> None:
    with pytest.raises(ParseError, match="malformed tag"):
        tokenize("0 @bad\n")


def test_famc_detail_without_pointer_is_skipped() -> None:
    # A FAMC carrying membership detail but no pointer value is tolerated
    # (skipped) rather than crashing the child-link lift pass.
    doc = read_text(_doc("0 @I1@ INDI\n1 FAMC\n2 PEDI BIRTH\n"))
    assert len(doc.records) == 1
