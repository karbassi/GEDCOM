"""The CLI entry point: subcommand dispatch, exit codes, and file output."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from gedcom7.cli import build_document, main
from gedcom7.cli.reader import read_document
from gedcom7.cli.scaffold import scaffold

_DOC = '{"individuals": [{"xref": "I1", "name": "Jane /Doe/", "sex": "F"}]}'


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    assert "gedcom7" in capsys.readouterr().out


def test_no_command_is_usage_error() -> None:
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code == 2


def test_build_to_ged_writes_bom(tmp_path: Path) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    out = tmp_path / "out.ged"
    assert main(["build", str(src), "-o", str(out)]) == 0
    data = out.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert b"0 @I1@ INDI" in data


def test_build_to_gdz_packages_zip(tmp_path: Path) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    out = tmp_path / "out.gdz"
    assert main(["build", str(src), "-o", str(out)]) == 0
    with zipfile.ZipFile(out) as archive:
        assert "gedcom.ged" in archive.namelist()


def test_build_to_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    assert main(["build", str(src)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("0 HEAD\n")
    assert "0 @I1@ INDI\n" in out


def test_build_unknown_output_extension(tmp_path: Path) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    assert main(["build", str(src), "-o", str(tmp_path / "out.xml")]) == 2


def test_build_load_error_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", '{"families": [{"husband": "I9"}]}')
    assert main(["build", str(src), "-o", str(tmp_path / "out.ged")]) == 2
    assert "matches no record" in capsys.readouterr().err


def test_validate_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    assert main(["validate", str(src)]) == 0
    assert "valid" in capsys.readouterr().out


def test_validate_load_error_exits_2(tmp_path: Path) -> None:
    src = _write(tmp_path, "in.json", '{"individuals": [{"name": "A /B/", "sex": "no"}]}')
    assert main(["validate", str(src)]) == 2


@pytest.mark.parametrize("fmt", ["yaml", "toml", "json"])
def test_init_templates_build(tmp_path: Path, fmt: str) -> None:
    if fmt == "yaml":
        pytest.importorskip("yaml")
    template = scaffold(fmt)
    path = _write(tmp_path, f"tree.{fmt}", template)
    document = build_document(read_document(path))
    from gedcom7 import validate

    assert validate(document, strict=True) == []


def test_init_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["init", "-f", "json"]) == 0
    assert '"individuals"' in capsys.readouterr().out


def test_init_to_file(tmp_path: Path) -> None:
    out = tmp_path / "tree.toml"
    assert main(["init", "-f", "toml", "-o", str(out)]) == 0
    assert out.exists()
    assert "[[individuals]]" in out.read_text(encoding="utf-8")
