"""Round-trip oracle for the reader (PRD: gedcom-reader, slice 01).

The contract is that the reader is the inverse of the writer for any document
the writer accepts: re-serializing a parsed document reproduces the original
text byte-for-byte. ``assert_roundtrips`` is the reusable harness later slices
build on; this module's own cases cover the tracer-bullet subset (minimal
HEAD+TRLR) plus the tokenizer's ``CONT`` and leading-``@`` handling.
"""

from __future__ import annotations

import pytest

import gedcom
from gedcom import Document, Header
from gedcom.lines import Line, render
from gedcom.parse import ParseError, read_text
from gedcom.parse._tokenize import tokenize


def assert_roundtrips(document: Document) -> None:
    """Assert ``write(read(write(doc)))`` is byte-identical to ``write(doc)``."""
    text = gedcom.dumps(document)
    reparsed = read_text(text)
    assert gedcom.dumps(reparsed) == text


def test_minimal_document_roundtrips() -> None:
    assert_roundtrips(Document())


def test_header_version_roundtrips() -> None:
    assert_roundtrips(Document(header=Header(gedcom_version="7.0")))


def test_read_text_returns_document() -> None:
    doc = read_text("0 HEAD\n1 GEDC\n2 VERS 7.0\n0 TRLR\n")
    assert isinstance(doc, Document)
    assert doc.header.gedcom_version == "7.0"
    assert doc.records == []


def test_read_text_tolerates_leading_bom() -> None:
    doc = read_text("﻿0 HEAD\n1 GEDC\n2 VERS 7.0\n0 TRLR\n")
    assert doc.header.gedcom_version == "7.0"


def test_tokenize_reassembles_cont_into_one_value() -> None:
    # A two-line value rendered with CONT must tokenize back to one '\n'-joined
    # logical value (the inverse of render_line's CONT splitting).
    text = render([Line(0, "HEAD"), Line(1, "NOTE", "line one\nline two"), Line(0, "TRLR")])
    lines = tokenize(text)
    note = next(line for line in lines if line.tag == "NOTE")
    assert note.value == "line one\nline two"


def test_tokenize_unescapes_leading_at() -> None:
    # Text beginning with '@' is rendered as '@@…'; tokenizing restores one '@'.
    text = render([Line(0, "HEAD"), Line(1, "NOTE", "@home"), Line(0, "TRLR")])
    lines = tokenize(text)
    note = next(line for line in lines if line.tag == "NOTE")
    assert note.value == "@home"
    assert note.is_pointer is False


def test_tokenize_classifies_pointer_value() -> None:
    lines = tokenize("0 @I1@ INDI\n1 FAMC @F1@\n0 TRLR\n")
    famc = next(line for line in lines if line.tag == "FAMC")
    assert famc.is_pointer is True
    assert famc.value == "@F1@"


def test_malformed_line_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        read_text("this is not a gedcom line\n")


def test_unknown_top_level_record_raises() -> None:
    # The tracer bullet only knows HEAD/TRLR; an unhandled level-0 tag is a
    # strict error until a later slice teaches the reader that record.
    with pytest.raises(ParseError):
        read_text("0 HEAD\n1 GEDC\n2 VERS 7.0\n0 @X1@ _UNKNOWN\n0 TRLR\n")
