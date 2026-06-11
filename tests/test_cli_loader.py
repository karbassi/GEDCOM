"""The loader: authoring mapping → Document → GEDCOM text."""

from __future__ import annotations

from typing import Any

import pytest

from gedcom import dumps, validate
from gedcom.cli import build_document
from gedcom.cli.errors import LoadError


def _build(mapping: dict[str, Any]) -> str:
    return dumps(build_document(mapping), strict=False)


def test_minimal_individual() -> None:
    out = _build({"individuals": [{"name": "Jane /Doe/", "sex": "F"}]})
    assert "0 HEAD\n" in out
    assert "1 NAME Jane /Doe/\n2 GIVN" not in out  # no pieces unless asked
    assert "INDI\n1 NAME Jane /Doe/\n1 SEX F\n" in out
    assert out.rstrip().endswith("0 TRLR")


def test_name_pieces_and_type() -> None:
    out = _build(
        {
            "individuals": [
                {
                    "name": {
                        "value": "Dr Jo /Doe/ Jr",
                        "type": "birth",
                        "pieces": {"given": ["Jo"], "surname": ["Doe"], "prefix": ["Dr"]},
                    }
                }
            ]
        }
    )
    assert "2 TYPE BIRTH\n" in out
    assert "2 GIVN Jo\n" in out
    assert "2 NPFX Dr\n" in out


def test_event_with_date_and_place_omits_y_payload() -> None:
    out = _build(
        {
            "individuals": [
                {
                    "name": "A /B/",
                    "events": [{"tag": "BIRT", "date": "1 JAN 1900", "place": "Boston, MA"}],
                }
            ]
        }
    )
    assert "1 BIRT\n2 DATE 1 JAN 1900\n3 TIME" not in out
    assert "1 BIRT\n2 DATE 1 JAN 1900\n2 PLAC Boston, MA\n" in out


def test_bare_event_asserts_occurred() -> None:
    out = _build({"individuals": [{"name": "A /B/", "events": [{"tag": "DEAT"}]}]})
    assert "1 DEAT Y\n" in out


def test_attribute_with_type() -> None:
    out = _build(
        {"individuals": [{"name": "A /B/", "attributes": [{"tag": "OCCU", "value": "Baker"}]}]}
    )
    assert "1 OCCU Baker\n" in out


def test_forward_reference_resolves() -> None:
    # The family references I1 before the individual is defined.
    mapping = {
        "families": [{"xref": "F1", "husband": "I1"}],
        "individuals": [{"xref": "I1", "name": "A /B/"}],
    }
    out = _build(mapping)
    assert "0 @I1@ INDI\n" in out
    assert "1 FAMS @F1@\n" in out  # derived back-pointer
    assert "0 @F1@ FAM\n1 HUSB @I1@\n" in out


def test_family_children_and_derived_famc() -> None:
    out = _build(
        {
            "individuals": [
                {"xref": "I1", "name": "P /Q/"},
                {"xref": "I2", "name": "C /Q/"},
            ],
            "families": [{"xref": "F1", "husband": "I1", "children": ["I2"]}],
        }
    )
    assert "0 @I2@ INDI\n1 NAME C /Q/\n1 FAMC @F1@\n" in out
    assert "0 @F1@ FAM\n1 HUSB @I1@\n1 CHIL @I2@\n" in out


def test_child_link_pedigree_and_status() -> None:
    out = _build(
        {
            "individuals": [
                {"xref": "I1", "name": "P /Q/"},
                {"xref": "I2", "name": "C /Q/"},
            ],
            "families": [
                {
                    "xref": "F1",
                    "husband": "I1",
                    "children": [{"individual": "I2", "pedigree": "adopted", "status": "proven"}],
                }
            ],
        }
    )
    assert "1 FAMC @F1@\n2 PEDI ADOPTED\n2 STAT PROVEN\n" in out


def test_at_wrapped_handles_tolerated() -> None:
    out = _build(
        {
            "individuals": [{"xref": "I1", "name": "A /B/"}],
            "families": [{"xref": "F1", "husband": "@I1@"}],
        }
    )
    assert "1 HUSB @I1@\n" in out


def test_dangling_reference_is_located_error() -> None:
    with pytest.raises(LoadError) as info:
        build_document({"families": [{"husband": "I9"}]})
    assert "families[0].husband" in str(info.value)
    assert "matches no record" in str(info.value)


def test_wrong_typed_reference() -> None:
    with pytest.raises(LoadError, match="expected Individual"):
        build_document({"sources": [{"xref": "S1"}], "families": [{"husband": "S1"}]})


def test_enum_accepts_name_and_spec_value() -> None:
    assert "1 SEX F\n" in _build({"individuals": [{"name": "A /B/", "sex": "female"}]})
    assert "1 SEX F\n" in _build({"individuals": [{"name": "A /B/", "sex": "F"}]})


def test_enum_extension_value_passthrough() -> None:
    out = _build({"individuals": [{"name": "A /B/", "sex": "_OTHER"}]})
    assert "1 SEX _OTHER\n" in out


def test_unknown_enum_value_located() -> None:
    with pytest.raises(LoadError) as info:
        build_document({"individuals": [{"name": "A /B/", "sex": "purple"}]})
    assert "individuals[0].sex" in str(info.value)
    assert "allowed:" in str(info.value)


def test_duplicate_handle_rejected() -> None:
    with pytest.raises(LoadError, match="duplicate handle"):
        build_document(
            {"individuals": [{"xref": "I1", "name": "A /B/"}, {"xref": "I1", "name": "C /D/"}]}
        )


def test_header_defaults_a_source() -> None:
    out = _build({"individuals": [{"name": "A /B/"}]})
    assert "1 SOUR gedcom\n" in out


def test_maximal_document_has_no_validator_issues() -> None:
    mapping = {
        "header": {
            "source": {"product": "Tester", "version": "1", "corporation": "Corp"},
            "language": "en",
            "copyright": "(c)",
            "submitter": "U1",
            "date": "1 JAN 2024",
            "place_form": "City, Country",
        },
        "submitters": [{"xref": "U1", "name": "Sub", "address": "1 St"}],
        "individuals": [
            {
                "xref": "I1",
                "name": {
                    "value": "Jo /Doe/",
                    "type": "birth",
                    "pieces": {"given": ["Jo"], "surname": ["Doe"]},
                    "translations": [{"value": "Yo /Doe/", "language": "fr"}],
                },
                "sex": "M",
                "restrictions": ["locked"],
                "attributes": [{"tag": "OCCU", "value": "Baker", "date": "1920"}],
                "events": [
                    {
                        "tag": "BIRT",
                        "date": "1 JAN 1900",
                        "place": {
                            "names": "Boston, MA",
                            "form": "City, State",
                            "map": [42.36, -71.06],
                        },
                        "age": "0y",
                    },
                    {"tag": "DEAT", "age": "72y", "age_phrase": "abt"},
                ],
                "associations": [{"person": "I2", "role": "friend"}],
                "notes": ["a note", {"ref": "N1"}],
                "sources": [{"source": "S1", "page": "p1", "quality": "direct", "role": "witness"}],
                "media": [{"multimedia": "O1", "title": "t"}],
                "identifiers": [{"kind": "EXID", "value": "x", "type": "afn"}],
                "change_date": {"date": "1 JAN 2020"},
            },
            {"xref": "I2", "name": "Mary /Roe/", "sex": "F"},
            {"xref": "I3", "name": "Kid /Doe/"},
        ],
        "families": [
            {
                "xref": "F1",
                "husband": "I1",
                "wife": "I2",
                "children": ["I3"],
                "events": [{"tag": "MARR", "date": "1925", "husband_age": "25y"}],
            }
        ],
        "sources": [
            {
                "xref": "S1",
                "title": "Vitals",
                "repository_citations": [{"repository": "R1", "call_numbers": ["c1"]}],
            }
        ],
        "repositories": [
            {"xref": "R1", "name": "Archive", "address": {"value": "1 St", "city": "C"}}
        ],
        "multimedia": [
            {"xref": "O1", "files": [{"path": "p.jpg", "form": "image/jpeg", "medium": "photo"}]}
        ],
        "shared_notes": [{"xref": "N1", "text": "shared"}],
    }
    document = build_document(mapping)
    assert validate(document, strict=True) == []
    text = dumps(document)
    assert "3 MAP\n4 LATI N42.36\n4 LONG W71.06\n" in text
    assert "1 EXID x\n2 TYPE https://gedcom.io/terms/v7/AFN\n" in text
    assert "2 HUSB\n3 AGE 25y\n" in text
