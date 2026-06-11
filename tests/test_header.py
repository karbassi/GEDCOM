from __future__ import annotations

from gedcom7 import Document, Header, dumps


def test_header_copyright_single_line() -> None:
    doc = Document(Header(copyright="© 2026 Example"))
    assert dumps(doc) == ("0 HEAD\n1 GEDC\n2 VERS 7.0\n1 COPR © 2026 Example\n0 TRLR\n")


def test_header_copyright_multiline_uses_cont() -> None:
    doc = Document(Header(copyright="Line A\nLine B"))
    assert dumps(doc) == ("0 HEAD\n1 GEDC\n2 VERS 7.0\n1 COPR Line A\n2 CONT Line B\n0 TRLR\n")


def test_header_without_copyright_omits_line() -> None:
    assert "COPR" not in dumps(Document())
