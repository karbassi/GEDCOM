"""The CLI entry point: subcommand dispatch, exit codes, and file output."""

from __future__ import annotations

import json
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
    out = capsys.readouterr().out
    assert out.startswith("gedcom ")
    assert "gedcom7" not in out  # the command is named 'gedcom', not 'gedcom7'


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "usage: gedcom" in out
    assert "build" in out and "validate" in out


def test_help_command_lists_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["help"]) == 0
    assert "usage: gedcom" in capsys.readouterr().out


def test_help_topic_shows_subcommand_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["help", "build"]) == 0
    out = capsys.readouterr().out
    assert "usage: gedcom build" in out
    assert "--lenient" in out


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


# -- AI-native surface: schema, guide, and structured --json output ----------


def test_schema_json_is_parseable_and_live(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    sections = {section["key"] for section in schema["sections"]}
    assert {"individuals", "families", "sources"} <= sections
    # Enum vocab is derived live from the enum classes.
    assert schema["enums"]["sex"]["values"]["female"] == "F"
    assert "individuals" in schema["example"]


def test_schema_text_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema", "-f", "text"]) == 0
    out = capsys.readouterr().out
    assert "authoring dialect" in out
    assert "sex:" in out


def test_guide_prints_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["guide"]) == 0
    out = capsys.readouterr().out
    assert "Workflow" in out
    assert "validate" in out


def test_validate_json_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    assert main(["validate", str(src), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"ok": True, "issues": []}


def test_validate_json_error_is_structured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = _write(tmp_path, "in.json", '{"individuals": [{"name": "A /B/", "sex": "no"}]}')
    assert main(["validate", str(src), "--json"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False
    assert result["error"]["path"] == "individuals[0].sex"
    assert "sex" in result["error"]["message"]


def test_build_json_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    out = tmp_path / "out.ged"
    assert main(["build", str(src), "-o", str(out), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["format"] == "gedcom"
    assert result["records"] == 1


def test_build_json_requires_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", _DOC)
    assert main(["build", str(src), "--json"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False
