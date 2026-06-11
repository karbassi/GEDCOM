"""Coverage for the CLI: the authoring-dialect loader's full field surface and
error branches, the date helpers, the document reader, scaffolding, and the
``main`` entry point's command/exit-code paths.
"""

from __future__ import annotations

import datetime as _dt
import json
import runpy
import sys
from pathlib import Path

import pytest

import gedcom
from gedcom import Individual
from gedcom.cli import build_document, main
from gedcom.cli.dates import parse_date, parse_date_exact
from gedcom.cli.errors import LoadError
from gedcom.cli.loader import build_document as load
from gedcom.cli.reader import read_document
from gedcom.cli.scaffold import scaffold

# --- kitchen-sink authoring document ----------------------------------------

KITCHEN_SINK: dict[str, object] = {
    "gedcom_version": "7.0",
    "header": {
        "source": {
            "product": "App",
            "version": "1.0",
            "full_name": "The App",
            "corporation": "Acme",
        },
        "destination": "Other",
        "date": "1 JAN 2024",
        "time": "09:30:00.5Z",
        "submitter": "U1",
        "language": "en",
        "place_form": ["City", "Country"],
        "copyright": "(c) 2024",
        "note": {"text": "header note", "language": "en"},
        "schema": {"_FLAG": "https://example.com/flag"},
    },
    "submitters": [
        {
            "xref": "U1",
            "name": "Pat",
            "address": {
                "value": "1 Main",
                "city": "Town",
                "state": "ST",
                "postal_code": "00000",
                "country": "USA",
            },
            "phones": ["555-1"],
            "emails": ["a@b.c"],
            "faxes": ["555-2"],
            "www": ["https://example.com"],
            "media": ["O1"],
            "notes": ["a note"],
            "identifiers": [{"kind": "REFN", "value": "1", "type": "local"}],
        }
    ],
    "individuals": [
        {
            "xref": "I1",
            "names": [
                {
                    "value": "Dr. John /Smith/ Jr.",
                    "type": "BIRTH",
                    "type_phrase": "the birth name",
                    "pieces": {
                        "prefix": ["Dr."],
                        "given": ["John"],
                        "surname": ["Smith"],
                        "suffix": ["Jr."],
                    },
                    "translations": [
                        {"value": "Jean /Smith/", "language": "fr", "pieces": {"given": ["Jean"]}}
                    ],
                }
            ],
            "sex": "M",
            "restrictions": ["CONFIDENTIAL"],
            "attributes": [
                {"tag": "OCCU", "value": "Baker", "agency": "Guild", "age": 40},
                {"tag": "IDNO", "value": "X9", "type": "badge"},
            ],
            "events": [
                {
                    "tag": "BIRT",
                    "date": "1 JAN 1900",
                    "time": {"hour": 8, "minute": 30, "second": 1, "fraction": 5, "utc": True},
                    "date_phrase": "early",
                    "sort_date": "2 JAN 1900",
                    "sort_time": "09:00",
                    "sort_phrase": "guess",
                    "age": "0y",
                    "age_phrase": "newborn",
                    "place": {
                        "names": ["Boston", "MA", "USA"],
                        "form": ["City", "State", "Country"],
                        "language": "en",
                        "translations": [{"names": ["Bostono"], "language": "eo"}],
                        "map": {"latitude": 42.36, "longitude": -71.06},
                    },
                    "address": "1 Birth St",
                    "phones": ["555-3"],
                    "agency": "Hospital",
                    "religion": "None",
                    "cause": "natural",
                },
                {
                    "tag": "ADOP",
                    "occurred": True,
                    "family_child": "F1",
                    "adopting_parent": "BOTH",
                    "adopting_parent_phrase": "both",
                },
                {"tag": "EVEN", "text": "Won a prize", "type": "Award"},
            ],
            "non_events": [{"tag": "MARR", "date": "FROM 1900 TO 1910", "date_phrase": "never"}],
            "ordinances": [
                {
                    "tag": "SLGC",
                    "family": "F1",
                    "detail": {
                        "date": "1 JAN 1990",
                        "time": "10:00",
                        "date_phrase": "morning",
                        "temple": "SLAKE",
                        "place": ["Temple", "UT"],
                        "status": "COMPLETED",
                        "status_date": "2 JAN 1990",
                        "status_time": "11:00",
                    },
                }
            ],
            "associations": [
                {
                    "person": "I2",
                    "role": "FRIEND",
                    "phrase": "best friend",
                    "role_phrase": "the friend",
                    "notes": ["assoc note"],
                    "sources": ["S1"],
                },
                {"person": "@VOID@", "role": "OTHER", "phrase": "unknown"},
            ],
            "aliases": [{"individual": "I2", "phrase": "aka"}],
            "ancestor_interest": ["U1"],
            "descendant_interest": ["U1"],
            "notes": [
                {
                    "text": "inline",
                    "mime": "text/plain",
                    "translations": [{"text": "t", "language": "fr"}],
                },
                "N1",
            ],
            "sources": [
                {
                    "source": "S1",
                    "page": "p.1",
                    "data_date": "1901",
                    "data_texts": ["t1", "t2"],
                    "event": "BIRT",
                    "event_phrase": "the birth",
                    "role": "WITNESS",
                    "role_phrase": "saw it",
                    "quality": "3",
                    "notes": ["cite note"],
                    "media": ["O1"],
                }
            ],
            "media": [
                {
                    "multimedia": "O1",
                    "crop": {"top": 1, "left": 2, "height": 3, "width": 4},
                    "title": "portrait",
                }
            ],
            "identifiers": [
                {"kind": "EXID", "value": "e", "type": "https://example.com/exid"},
                {"kind": "UID", "value": "u"},
            ],
            "change_date": {"date": "1 JUN 2020", "time": "12:00", "notes": ["changed"]},
            "creation_date": {"date": "1 JAN 2019", "time": {"hour": 1, "minute": 2}},
        },
        {"xref": "I2", "name": "Mary /Jones/", "sex": "F"},
        {"xref": "I3", "name": "Sara /Smith/"},
    ],
    "families": [
        {
            "xref": "F1",
            "husband": "I1",
            "wife": "I2",
            "children": [
                {"individual": "I3", "pedigree": "BIRTH", "status": "PROVEN"},
                "@VOID@",
            ],
            "restrictions": ["LOCKED"],
            "attributes": [{"tag": "NCHI", "value": "2"}],
            "events": [
                {"tag": "MARR", "date": "5 JUN 1925", "husband_age": "25y", "wife_age": "23y"}
            ],
            "sealings": [{"detail": {"date": "1 JAN 1985", "temple": "LOGAN"}}],
            "notes": ["fam note"],
        }
    ],
    "sources": [
        {
            "xref": "S1",
            "author": "Auth",
            "title": "Title",
            "abbr": "T",
            "publ": "Pub",
            "text": "body",
            "text_mime": "text/plain",
            "text_lang": "en",
            "data": {
                "events": [
                    {
                        "events": ["BIRT", "DEAT"],
                        "date": "FROM 1800 TO 1850",
                        "date_phrase": "span",
                        "place": "Town",
                    }
                ],
                "agency": "Agency",
                "notes": ["data note"],
            },
            "repositories": [
                {"repository": "R1", "call_numbers": [{"value": "A.1", "medium": "BOOK"}, "B.2"]}
            ],
        }
    ],
    "repositories": [
        {"xref": "R1", "name": "Archive", "address": "1 Archive Rd", "phone": "555-4"}
    ],
    "multimedia": [
        {
            "xref": "O1",
            "files": [
                {
                    "path": "a.jpg",
                    "form": "image/jpeg",
                    "medium": "PHOTO",
                    "title": "A",
                    "translations": [{"path": "a.png", "form": "image/png"}],
                }
            ],
            "restrictions": ["PRIVACY"],
        }
    ],
    "shared_notes": [
        {
            "xref": "N1",
            "text": "shared",
            "mime": "text/plain",
            "language": "en",
            "translations": [{"text": "partagé", "language": "fr"}],
        }
    ],
}


def test_kitchen_sink_builds_and_round_trips() -> None:
    doc = load(KITCHEN_SINK)
    text = gedcom.dumps(doc, strict=False)
    # And the GEDCOM reader round-trips the writer's output.
    assert gedcom.dumps(gedcom.read_text(text), strict=False) == text


def test_kitchen_sink_map_as_list_and_age_dict() -> None:
    doc = load(
        {
            "individuals": [
                {
                    "xref": "I1",
                    "events": [
                        {
                            "tag": "BIRT",
                            "place": {"names": ["X"], "map": [12.0, 34.0]},
                            "age": {"years": 1, "months": 2, "bound": ">"},
                        }
                    ],
                }
            ]
        }
    )
    assert doc.records


# --- loader error branches --------------------------------------------------


@pytest.mark.parametrize(
    "doc",
    [
        {"individuals": [{"xref": "I1", "non_events": [{"tag": "MARR", "date": "1 JAN 1900"}]}]},
        {"sources": [{"xref": "S1", "data": {"events": [{"events": ["BIRT"], "date": "1900"}]}}]},
        {
            "individuals": [
                {"xref": "I1", "events": [{"tag": "BIRT", "place": {"names": ["X"], "map": [1.0]}}]}
            ]
        },
        {
            "individuals": [
                {"xref": "I1", "events": [{"tag": "BIRT", "date": "1900", "time": "nope"}]}
            ]
        },
        {"individuals": [{"xref": "I1", "attributes": [{"tag": "X", "value": "v", "age": "bad"}]}]},
        {"individuals": "not a list"},
        {"individuals": [{"name": 5}]},
        {"header": {"note": {"shared": "N1"}}, "shared_notes": [{"xref": "N1", "text": "x"}]},
    ],
)
def test_loader_rejects(doc: dict[str, object]) -> None:
    with pytest.raises(LoadError):
        load(doc)


def test_loader_missing_required_field() -> None:
    with pytest.raises(LoadError, match="missing required"):
        load({"multimedia": [{"xref": "O1", "files": [{"form": "image/jpeg"}]}]})


def test_loader_unknown_reference() -> None:
    with pytest.raises(LoadError):
        load({"families": [{"xref": "F1", "husband": "I9"}]})


# --- date helpers -----------------------------------------------------------


def test_parse_date_accepts_datetime_and_date() -> None:
    assert parse_date(_dt.datetime(1900, 1, 2, 3, 4)) == gedcom.types.CalendarDate(1900, 1, 2)
    assert parse_date(_dt.date(1900, 1, 2)) == gedcom.types.CalendarDate(1900, 1, 2)


def test_parse_date_exact_accepts_datetime_and_date() -> None:
    assert parse_date_exact(_dt.datetime(1900, 1, 2)) == gedcom.types.DateExact(1900, 1, 2)
    assert parse_date_exact(_dt.date(1900, 1, 2)) == gedcom.types.DateExact(1900, 1, 2)


def test_parse_date_rejects_non_string() -> None:
    with pytest.raises(LoadError, match="date string"):
        parse_date(123)


def test_parse_date_exact_rejects_non_string() -> None:
    with pytest.raises(LoadError, match="exact date"):
        parse_date_exact(123)


def test_parse_date_errors() -> None:
    with pytest.raises(LoadError, match="missing a date"):
        parse_date("ABT")
    with pytest.raises(LoadError, match="missing a year"):
        parse_date("BCE")
    with pytest.raises(LoadError, match="too many parts"):
        parse_date("1 2 3 4 5")
    with pytest.raises(LoadError, match="not a valid"):
        parse_date("x JAN 1900")


# --- document reader --------------------------------------------------------


def test_read_document_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LoadError, match="cannot read"):
        read_document(tmp_path / "missing.json")


def test_read_document_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "x.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(LoadError, match="invalid JSON"):
        read_document(bad)


def test_read_document_bad_toml(tmp_path: Path) -> None:
    bad = tmp_path / "x.toml"
    bad.write_text("= = =", encoding="utf-8")
    with pytest.raises(LoadError, match="invalid TOML"):
        read_document(bad)


def test_read_document_bad_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "x.yaml"
    bad.write_text("a: : :\n- broken", encoding="utf-8")
    with pytest.raises(LoadError, match="invalid YAML"):
        read_document(bad)


def test_read_document_unsupported_extension(tmp_path: Path) -> None:
    bad = tmp_path / "x.xml"
    bad.write_text("<x/>", encoding="utf-8")
    with pytest.raises(LoadError, match="unsupported input extension"):
        read_document(bad)


def test_read_document_non_mapping_root(tmp_path: Path) -> None:
    bad = tmp_path / "x.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(LoadError, match="must be a mapping"):
        read_document(bad)


# --- scaffold ----------------------------------------------------------------


def test_scaffold_unknown_format() -> None:
    with pytest.raises(LoadError, match="unknown init format"):
        scaffold("xml")


# --- main entry point --------------------------------------------------------


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_main_build_input_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", '{"individuals": "not a list"}')
    assert main(["build", str(src)]) == 2
    assert capsys.readouterr().err


def test_main_validate_reports_issues(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A family child not added to the document yields a validation issue.
    src = _write(
        tmp_path, "in.json", '{"individuals": [{"xref": "I1", "events": [{"tag": "EVEN"}]}]}'
    )
    code = main(["validate", str(src)])
    assert code == 1
    assert capsys.readouterr().err


def test_main_validate_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.json", '{"individuals": [{"xref": "I1", "name": "A /B/"}]}')
    assert main(["validate", str(src)]) == 0
    assert "valid" in capsys.readouterr().out


def test_main_schema_json_schema(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema", "--format", "json-schema"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["$schema"].startswith("https://json-schema.org/")


def test_main_build_lenient_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # An EXID without a TYPE is deprecated; --lenient downgrades it to a warning.
    doc = '{"individuals": [{"xref": "I1", "identifiers": [{"kind": "EXID", "value": "x"}]}]}'
    src = _write(tmp_path, "in.json", doc)
    out = tmp_path / "out.ged"
    assert main(["build", str(src), "-o", str(out), "--lenient"]) == 0
    assert "warning:" in capsys.readouterr().err


def test_build_document_reexport_matches() -> None:
    # gedcom.cli.build_document is the same loader entry point.
    assert build_document is load


def test_python_m_gedcom_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    # `python -m gedcom` runs the CLI; with no args it prints help and exits 0.
    monkeypatch.setattr(sys, "argv", ["gedcom"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("gedcom", run_name="__main__")
    assert info.value.code == 0


def test_main_build_validation_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A generic EVEN with no text is a hard validation error; strict build
    # surfaces it as a ValidationError caught at the entry point.
    src = _write(
        tmp_path, "in.json", '{"individuals": [{"xref": "I1", "events": [{"tag": "EVEN"}]}]}'
    )
    assert main(["build", str(src)]) == 1
    assert capsys.readouterr().err


# --- remaining loader scalar/alternate-form branches ------------------------


def test_loader_scalar_coercions_and_alternate_forms() -> None:
    doc = load(
        {
            "individuals": [
                {
                    "xref": "I1",
                    "events": [
                        {
                            "tag": "BIRT",
                            "place": {
                                "names": 1900,
                                "map": ["42.0", "-71.0"],
                            },  # _text_list scalar, _float text
                            "phones": [555],  # _text on an int
                        }
                    ],
                    "media": [
                        {"multimedia": "O1", "crop": {"top": "3"}}
                    ],  # _int from a digit string
                    "identifiers": [
                        {"kind": "EXID", "value": "x", "type": "afn"}
                    ],  # ExidType member
                }
            ],
            "individuals_extra": None,
            "multimedia": [{"xref": "O1", "files": [{"path": "a.jpg", "form": "image/jpeg"}]}],
            "sources": [{"xref": "S1", "repositories": ["R1"]}],  # repo-citation string form
            "repositories": [{"xref": "R1", "name": "Repo"}],
            "header": {"source": "JustAName"},  # header source string form
        }
    )
    assert {r.xref_id for r in doc.records} >= {"I1", "O1", "S1", "R1"}


@pytest.mark.parametrize(
    "doc",
    [
        {"individuals": [{"xref": "I1", "events": [{"tag": "BIRT", "occurred": "yes"}]}]},  # _bool
        {
            "individuals": [{"xref": "I1", "associations": [{"person": "I1"}]}]
        },  # _enum_required missing role
        {
            "individuals": [
                {"xref": "I1", "identifiers": [{"kind": "EXID", "value": "x", "type": "bogus"}]}
            ]
        },
        {
            "individuals": [
                {
                    "xref": "I1",
                    "events": [
                        {"tag": "BIRT", "place": {"names": ["X"], "map": {"latitude": 1.0}}}
                    ],
                }
            ]
        },
        {
            "individuals": [
                {"xref": "I1", "events": [{"tag": "BIRT", "date": "1900", "phones": [[1]]}]}
            ]
        },  # _text non-text
        {
            "individuals": [{"xref": "I1", "media": [{"multimedia": "O1", "crop": {"top": 1.5}}]}],
            "multimedia": [{"xref": "O1", "files": [{"path": "a", "form": "b"}]}],
        },  # _int bad
        {
            "individuals": [
                {
                    "xref": "I1",
                    "events": [{"tag": "BIRT", "place": {"names": ["X"], "map": ["abc", "def"]}}],
                }
            ]
        },  # _float bad
    ],
)
def test_loader_more_rejections(doc: dict[str, object]) -> None:
    with pytest.raises(LoadError):
        load(doc)


def test_media_link_without_ref_is_void() -> None:
    # A media link with no multimedia reference resolves to the void pointer.
    doc = load({"individuals": [{"xref": "I1", "media": [{"title": "untethered"}]}]})
    indi = doc.records[0]
    assert isinstance(indi, Individual)
    assert indi.media_links[0].title == "untethered"


def test_alias_and_void_resolution_roundtrip() -> None:
    # alias as string + void association exercise _resolve / _resolve_or_void.
    doc = load(
        {
            "individuals": [
                {
                    "xref": "I1",
                    "aliases": ["I2"],
                    "associations": [{"person": "@VOID@", "role": "OTHER"}],
                },
                {"xref": "I2"},
            ]
        }
    )
    assert len(doc.records) == 2


# --- standalone time/age string parsers -------------------------------------


def test_loader_time_with_seconds_no_fraction() -> None:
    doc = load(
        {
            "individuals": [
                {"xref": "I1", "events": [{"tag": "BIRT", "date": "1900", "time": "10:00:30"}]}
            ]
        }
    )
    indi = doc.records[0]
    assert isinstance(indi, Individual)
    assert indi.events[0].detail is not None
    assert indi.events[0].detail.date_time == gedcom.types.Time(10, 0, 30)


def test_loader_age_bound_and_empty() -> None:
    doc = load(
        {"individuals": [{"xref": "I1", "attributes": [{"tag": "X", "value": "v", "age": "> 5y"}]}]}
    )
    indi = doc.records[0]
    assert isinstance(indi, Individual)
    assert indi.attributes[0].detail is not None
    assert indi.attributes[0].detail.age == gedcom.types.Age(years=5, bound=">")
    with pytest.raises(LoadError, match="empty age"):
        load(
            {
                "individuals": [
                    {"xref": "I1", "attributes": [{"tag": "X", "value": "v", "age": "  "}]}
                ]
            }
        )
