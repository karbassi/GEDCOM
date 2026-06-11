from __future__ import annotations

import pytest

from gedcom7 import Document, Header, Submitter, ValidationError, dumps
from gedcom7.xref import VOID, XrefError, build_xref_table


def test_full_submitter_document_golden() -> None:
    subm = Submitter("Ali Karbassi")
    doc = Document(Header(submitter=subm), records=[subm])
    assert dumps(doc) == (
        "0 HEAD\n1 GEDC\n2 VERS 7.0\n1 SUBM @U1@\n0 @U1@ SUBM\n1 NAME Ali Karbassi\n0 TRLR\n"
    )


def test_xref_deterministic_and_unique() -> None:
    a, b = Submitter("A"), Submitter("B")
    table = build_xref_table(Document(records=[a, b]))
    assert table.of(a) == "@U1@"
    assert table.of(b) == "@U2@"


def test_xref_override_is_honored() -> None:
    a = Submitter("A", xref_id="ME")
    b = Submitter("B")
    table = build_xref_table(Document(records=[a, b]))
    assert table.of(a) == "@ME@"
    assert table.of(b) == "@U1@"


def test_void_pointer() -> None:
    table = build_xref_table(Document())
    assert table.resolve(VOID) == "@VOID@"


def test_reference_to_unadded_record_raises() -> None:
    subm = Submitter("X")
    doc = Document(Header(submitter=subm))  # submitter not in records
    with pytest.raises(ValidationError, match="not added"):
        dumps(doc)


def test_duplicate_override_raises() -> None:
    a = Submitter("A", xref_id="DUP")
    b = Submitter("B", xref_id="DUP")
    with pytest.raises(XrefError, match="duplicate"):
        build_xref_table(Document(records=[a, b]))


def test_submitter_contacts() -> None:
    subm = Submitter("A", phones=["+1 555 0100"], emails=["a@b.co"], web_pages=["x"])
    out = dumps(Document(records=[subm]))
    assert "1 PHON +1 555 0100\n" in out
    assert "1 EMAIL a@b.co\n" in out
    assert "1 WWW x\n" in out
