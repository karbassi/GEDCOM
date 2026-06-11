"""Registered `_`-prefixed extension structures + auto-SCHMA."""

from __future__ import annotations

import pytest

from gedcom7 import Document, ExtensionStructure, Submitter, dumps

_SOUR_URI = "https://github.com/dthaler/gedcom-citations/_SOUR"
_DATE_URI = "https://github.com/dthaler/gedcom-citations/_DATE"


def test_registered_extension_serializes_with_nested_children() -> None:
    subm = Submitter(
        "Ali",
        extensions=[
            ExtensionStructure(
                "_SOUR", children=(ExtensionStructure("_DATE", value="2024"),)
            )
        ],
    )
    out = dumps(Document(records=[subm]))
    assert "1 _SOUR\n2 _DATE 2024\n" in out


def test_registered_extension_auto_declares_schma_uris() -> None:
    subm = Submitter("Ali", extensions=[ExtensionStructure("_SOUR")])
    out = dumps(Document(records=[subm]))
    assert "1 SCHMA\n" in out
    assert f"2 TAG _SOUR {_SOUR_URI}\n" in out


def test_unregistered_extension_tag_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a registered extension structure"):
        ExtensionStructure("_NOPE")


def test_no_schma_when_no_extensions_used() -> None:
    out = dumps(Document(records=[Submitter("Ali")]))
    assert "SCHMA" not in out
