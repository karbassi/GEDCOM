"""Coverage for core-library branches not exercised elsewhere: value-type
invariants, validation issues, xref allocation edges, and a few writer paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gedcom
from gedcom import (
    VOID,
    Document,
    Event,
    Family,
    File,
    Identifier,
    Individual,
    Multimedia,
    Note,
    NoteTranslation,
    Source,
    SourceData,
    SourceDataEvent,
    dump_gedzip,
)
from gedcom.model import RecordBase
from gedcom.serialize import serialize_document
from gedcom.types import Age, ApproxDate, CalendarDate, DateExact, DateRange, Time
from gedcom.validation import ValidationError, validate
from gedcom.xref import XrefError, XrefTable, build_xref_table

# --- value-type invariants --------------------------------------------------


def test_calendar_date_day_out_of_range() -> None:
    with pytest.raises(ValueError, match="day"):
        CalendarDate(1900, 1, 40)


def test_date_exact_month_out_of_range() -> None:
    with pytest.raises(ValueError, match="month"):
        DateExact(2020, 13, 1)


def test_approx_date_unknown_kind() -> None:
    with pytest.raises(ValueError, match="approximation"):
        ApproxDate(CalendarDate(1900), "XYZ")


def test_date_range_needs_a_bound() -> None:
    with pytest.raises(ValueError, match="bound"):
        DateRange()


def test_time_invariants() -> None:
    with pytest.raises(ValueError, match="minute"):
        Time(1, 99)
    with pytest.raises(ValueError, match="second"):
        Time(1, 1, 99)
    with pytest.raises(ValueError, match="fractional second"):
        Time(1, 1, fraction=5)


def test_age_unknown_bound() -> None:
    with pytest.raises(ValueError, match="bound"):
        Age(years=1, bound="?")


def test_void_pointer_repr() -> None:
    assert repr(VOID) == "VOID"


# --- validation issues ------------------------------------------------------


def test_duplicate_xref_id_is_a_validation_error() -> None:
    doc = Document(records=[Individual(xref_id="I1"), Individual(xref_id="I1")])
    with pytest.raises(ValidationError, match="duplicate"):
        validate(doc, strict=True)


def test_generic_even_requires_text() -> None:
    doc = Document(records=[Individual(events=[Event("EVEN")])])
    issues = list(validate(doc, strict=False))
    assert any("generic EVEN" in m for m in issues)


def test_famc_child_not_in_document_is_flagged() -> None:
    orphan = Individual()
    fam = Family(children=[orphan])  # orphan is referenced but never added
    doc = Document(records=[fam])
    issues = list(validate(doc, strict=False))
    assert any("not added to the Document" in m for m in issues)


# --- xref allocation edges --------------------------------------------------


class _Unsupported(RecordBase):
    """A record type the xref/serialize layers do not know about."""


def test_unknown_record_type_has_no_xref_prefix() -> None:
    with pytest.raises(XrefError, match="no xref prefix"):
        build_xref_table(Document(records=[_Unsupported()]))


def test_serialize_rejects_unknown_record_type() -> None:
    record = _Unsupported()
    table = XrefTable()
    table._register(record, "@X1@")
    with pytest.raises(TypeError, match="no serializer"):
        list(serialize_document(Document(records=[record]), table))


def test_auto_xref_skips_a_pinned_collision() -> None:
    # The first individual pins @I1@; the second auto-assigns, collides on I1,
    # and the allocator advances past it.
    pinned = Individual(xref_id="I1")
    auto = Individual()
    table = build_xref_table(Document(records=[pinned, auto]))
    assert table.of(pinned) == "@I1@"
    assert table.of(auto) == "@I2@"


# --- writer branches --------------------------------------------------------


def test_family_attribute_and_source_event_phrase_render() -> None:
    from gedcom.types import DatePeriod

    fam = Family(xref_id="F1", attributes=[gedcom.Attribute("NCHI", "2")])
    src = Source(
        xref_id="S1",
        data=SourceData(
            events=[
                SourceDataEvent(
                    ["BIRT"], date=DatePeriod(start=CalendarDate(1800)), date_phrase="around then"
                )
            ]
        ),
    )
    text = gedcom.dumps(Document(records=[fam, src]))
    assert "1 NCHI 2" in text
    assert "4 PHRASE around then" in text
    assert gedcom.dumps(gedcom.read_text(text)) == text


def test_note_translation_mime_renders() -> None:
    note = Note("hi", translations=[NoteTranslation("salut", mime="text/plain", language="fr")])
    person = Individual(xref_id="I1", notes=[note])
    text = gedcom.dumps(Document(records=[person]))
    assert "3 MIME text/plain" in text
    assert gedcom.dumps(gedcom.read_text(text)) == text


# --- GEDZIP writer branches -------------------------------------------------


def test_gedzip_dedupes_colliding_media_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    # Three absolute paths all reduce to media/photo.jpg, forcing de-collision
    # twice (photo.jpg -> photo-1.jpg -> photo-2.jpg).
    files = []
    for sub, data in (("a", b"A"), ("b", b"B"), ("c", b"C")):
        (tmp_path / sub).mkdir()
        (tmp_path / sub / "photo.jpg").write_bytes(data)
        files.append(File(str(tmp_path / sub / "photo.jpg"), "image/jpeg"))
    obje = Multimedia(xref_id="O1", files=files)
    out = tmp_path / "t.gdz"
    dump_gedzip(Document(records=[obje]), out)
    import zipfile

    with zipfile.ZipFile(out) as archive:
        members = [n for n in archive.namelist() if n != "gedcom.ged"]
    assert sorted(members) == ["media/photo-1.jpg", "media/photo-2.jpg", "media/photo.jpg"]


def test_gedzip_warns_on_validation_message(tmp_path: Path) -> None:
    # An EXID without a TYPE is deprecated -> a validation warning the writer
    # surfaces; in lenient mode it warns rather than raising.
    doc = Document(records=[Multimedia(xref_id="O1", identifiers=[Identifier("EXID", "x")])])
    with pytest.warns(UserWarning):
        dump_gedzip(doc, tmp_path / "t.gdz", strict=False)
