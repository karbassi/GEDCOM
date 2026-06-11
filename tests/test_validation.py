from __future__ import annotations

import warnings

import pytest

from gedcom7 import (
    Document,
    Family,
    Header,
    Individual,
    PersonalName,
    Submitter,
    ValidationError,
    dumps,
    validate,
)


def test_valid_document_has_no_issues() -> None:
    subm = Submitter("Ali")
    assert validate(Document(Header(submitter=subm), records=[subm])) == []


def test_strict_raises_on_empty_submitter_name() -> None:
    with pytest.raises(ValidationError, match="non-empty NAME"):
        dumps(Document(records=[Submitter("")]))


def test_strict_raises_on_unresolved_family_member() -> None:
    husband = Individual(names=[PersonalName("A //")])
    fam = Family(husband=husband)  # husband not added to records
    with pytest.raises(ValidationError, match="HUSB points to an Individual not added"):
        dumps(Document(records=[fam]))


def test_strict_raises_on_duplicate_child() -> None:
    child = Individual(names=[PersonalName("C //")])
    fam = Family(children=[child, child])
    with pytest.raises(ValidationError, match="same Individual as a child"):
        dumps(Document(records=[child, fam]))


def test_lenient_mode_warns_and_emits() -> None:
    doc = Document(records=[Submitter("")])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = dumps(doc, strict=False)
    assert any("non-empty NAME" in str(w.message) for w in caught)
    assert "0 @U1@ SUBM" in out  # emitted anyway


def test_validate_returns_messages_in_lenient_mode() -> None:
    messages = validate(Document(records=[Submitter("")]), strict=False)
    assert messages == ["SUBM requires a non-empty NAME"]
