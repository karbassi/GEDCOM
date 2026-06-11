"""GEDZIP (.gdz) packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from gedcom import Document, File, GedzipError, Multimedia, dump_gedzip


def _ged_text(archive: zipfile.ZipFile) -> str:
    return archive.read("gedcom.ged").decode("utf-8-sig")


def test_packages_ged_and_local_media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "media").mkdir()
    (tmp_path / "media" / "photo.jpg").write_bytes(b"\xff\xd8jpegbytes")
    obje = Multimedia(files=[File(path="media/photo.jpg", form="image/jpeg")])

    out = tmp_path / "tree.gdz"
    dump_gedzip(Document(records=[obje]), out)

    with zipfile.ZipFile(out) as archive:
        assert "gedcom.ged" in archive.namelist()
        assert "media/photo.jpg" in archive.namelist()
        assert archive.read("media/photo.jpg") == b"\xff\xd8jpegbytes"
        assert "1 FILE media/photo.jpg\n" in _ged_text(archive)


def test_url_file_is_not_packaged(tmp_path: Path) -> None:
    obje = Multimedia(files=[File(path="https://ex/img.jpg", form="image/jpeg")])
    out = tmp_path / "t.gdz"
    dump_gedzip(Document(records=[obje]), out)
    with zipfile.ZipFile(out) as archive:
        assert archive.namelist() == ["gedcom.ged"]
        assert "1 FILE https://ex/img.jpg\n" in _ged_text(archive)


def test_missing_local_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    obje = Multimedia(files=[File(path="gone.jpg", form="image/jpeg")])
    with pytest.raises(GedzipError, match="does not exist"):
        dump_gedzip(Document(records=[obje]), tmp_path / "t.gdz")


def test_absolute_path_rewritten_to_archive_relative(
    tmp_path: Path,
) -> None:
    src = tmp_path / "photo.jpg"
    src.write_bytes(b"x")
    obje = Multimedia(files=[File(path=str(src), form="image/jpeg")])
    out = tmp_path / "t.gdz"
    dump_gedzip(Document(records=[obje]), out)
    with zipfile.ZipFile(out) as archive:
        assert "media/photo.jpg" in archive.namelist()
        assert "1 FILE media/photo.jpg\n" in _ged_text(archive)
