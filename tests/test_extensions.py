"""Registered `_`-prefixed extension structures + auto-SCHMA."""

from __future__ import annotations

import pytest

from gedcom import Document, ExtensionStructure, Submitter, dumps

_SOUR_URI = "https://github.com/dthaler/gedcom-citations/_SOUR"
_DATE_URI = "https://github.com/dthaler/gedcom-citations/_DATE"


def test_registered_extension_serializes_with_nested_children() -> None:
    subm = Submitter(
        "Ali",
        extensions=[
            ExtensionStructure("_SOUR", children=(ExtensionStructure("_DATE", value="2024"),))
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


def test_arbitrary_extension_with_user_uri() -> None:
    subm = Submitter(
        "Ali",
        extensions=[ExtensionStructure("_FOO", value="bar", uri="https://example/_FOO")],
    )
    out = dumps(Document(records=[subm]))
    assert "1 _FOO bar\n" in out
    assert "2 TAG _FOO https://example/_FOO\n" in out


def test_arbitrary_extension_requires_uri_or_registration() -> None:
    with pytest.raises(ValueError, match="pass uri="):
        ExtensionStructure("_FOO")


def test_extension_tag_must_start_with_underscore() -> None:
    with pytest.raises(ValueError, match="must start with"):
        ExtensionStructure("FOO", uri="https://example/FOO")


def test_validate_accepts_well_formed_extension() -> None:
    from gedcom import validate

    subm = Submitter("Ali", extensions=[ExtensionStructure("_SOUR")])
    assert validate(Document(records=[subm])) == []
