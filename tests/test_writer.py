from __future__ import annotations

from pathlib import Path

from gedcom import Document, Header, dump, dumps

MINIMAL = "0 HEAD\n1 GEDC\n2 VERS 7.0\n0 TRLR\n"


def test_minimal_document() -> None:
    assert dumps(Document(Header("7.0"))) == MINIMAL


def test_default_header_version() -> None:
    assert dumps(Document()) == MINIMAL


def test_dump_writes_bom_prefixed_utf8(tmp_path: Path) -> None:
    out = tmp_path / "out.ged"
    dump(Document(), out)
    data = out.read_bytes()
    assert data[:3] == b"\xef\xbb\xbf"
    assert data.decode("utf-8") == "﻿" + MINIMAL


def test_dumps_has_no_bom() -> None:
    assert not dumps(Document()).startswith("﻿")


def test_eol_is_selectable() -> None:
    assert dumps(Document(), eol="\r\n") == ("0 HEAD\r\n1 GEDC\r\n2 VERS 7.0\r\n0 TRLR\r\n")


def test_dump_to_binary_stream() -> None:
    import io

    buf = io.BytesIO()
    dump(Document(), buf)
    assert buf.getvalue().decode("utf-8") == "﻿" + MINIMAL
