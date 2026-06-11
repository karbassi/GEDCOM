"""GEDZIP / read_path round-trips and unzip guards (PRD: gedcom-reader, slice 07)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

import gedcom
from gedcom import (
    Document,
    File,
    Individual,
    Multimedia,
    PersonalName,
    dump,
    dump_gedzip,
    read_path,
)
from gedcom.parse import ParseError


def test_read_path_reads_ged_text(tmp_path: Path) -> None:
    doc = Document(records=[Individual(xref_id="I1", names=[PersonalName("A /B/")])])
    out = tmp_path / "tree.ged"
    dump(doc, out)
    reparsed = read_path(out)
    assert gedcom.dumps(reparsed) == gedcom.dumps(doc)


def test_read_path_reads_gedzip_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "media").mkdir()
    (tmp_path / "media" / "photo.jpg").write_bytes(b"\xff\xd8jpeg")
    obje = Multimedia(xref_id="O1", files=[File(path="media/photo.jpg", form="image/jpeg")])
    doc = Document(records=[obje])
    out = tmp_path / "tree.gdz"
    dump_gedzip(doc, out)

    reparsed = read_path(out)

    # The GEDCOM payload round-trips byte-for-byte against the archive member.
    with zipfile.ZipFile(out) as archive:
        member_text = archive.read("gedcom.ged").decode("utf-8-sig")
    assert gedcom.dumps(reparsed) == member_text

    # The media member is recovered and its archive-relative path is the one the
    # parsed Multimedia record now references.
    media = next(r for r in reparsed.records if isinstance(r, Multimedia))
    assert media.files[0].path == "media/photo.jpg"
    with zipfile.ZipFile(out) as archive:
        assert media.files[0].path in archive.namelist()


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)


def test_gedzip_without_gedcom_member_raises(tmp_path: Path) -> None:
    out = tmp_path / "bad.gdz"
    _write_zip(out, {"other.txt": b"hi"})
    with pytest.raises(ParseError, match=r"no 'gedcom\.ged'"):
        read_path(out)


def test_path_traversal_member_raises(tmp_path: Path) -> None:
    out = tmp_path / "evil.gdz"
    _write_zip(out, {"gedcom.ged": b"0 HEAD\n0 TRLR\n", "../escape.txt": b"x"})
    with pytest.raises(ParseError, match="unsafe archive member"):
        read_path(out)


def test_zip_bomb_total_size_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from gedcom.parse import _gedzip

    monkeypatch.setattr(_gedzip, "_MAX_TOTAL_BYTES", 16)
    out = tmp_path / "bomb.gdz"
    _write_zip(out, {"gedcom.ged": b"0 HEAD\n0 TRLR\n", "big.bin": b"\x00" * 4096})
    with pytest.raises(ParseError, match="zip bomb"):
        read_path(out)


def test_zip_bomb_ratio_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from gedcom.parse import _gedzip

    monkeypatch.setattr(_gedzip, "_MAX_RATIO", 2)
    monkeypatch.setattr(_gedzip, "_RATIO_FLOOR", 16)
    out = tmp_path / "bomb.gdz"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("gedcom.ged", b"0 HEAD\n0 TRLR\n")
        archive.writestr("squish.bin", b"\x00" * 4096)  # compresses far past 2:1
    with pytest.raises(ParseError, match="zip bomb"):
        read_path(out)
