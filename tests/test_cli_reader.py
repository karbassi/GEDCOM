"""The authoring-document format reader: extension dispatch + errors."""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any

import pytest

from gedcom.cli.errors import LoadError
from gedcom.cli.reader import read_document

_JSON = '{"individuals": [{"name": "A /B/"}]}'
_YAML = "individuals:\n  - name: A /B/\n"


def test_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    path.write_text(_JSON, encoding="utf-8")
    assert read_document(path) == {"individuals": [{"name": "A /B/"}]}


def test_reads_yaml(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    path = tmp_path / "doc.yaml"
    path.write_text(_YAML, encoding="utf-8")
    assert read_document(path) == {"individuals": [{"name": "A /B/"}]}


def test_unknown_extension_rejected(tmp_path: Path) -> None:
    path = tmp_path / "doc.xml"
    path.write_text("<x/>", encoding="utf-8")
    with pytest.raises(LoadError, match="unsupported input extension"):
        read_document(path)


def test_non_mapping_root_rejected(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(LoadError, match="must be a mapping"):
        read_document(path)


def test_missing_pyyaml_gives_actionable_error(tmp_path: Path, monkeypatch: Any) -> None:
    path = tmp_path / "doc.yaml"
    path.write_text(_YAML, encoding="utf-8")
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "yaml":
            raise ModuleNotFoundError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(LoadError, match=r"gedcom\[yaml\]"):
        read_document(path)
