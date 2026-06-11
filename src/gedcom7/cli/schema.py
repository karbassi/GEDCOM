"""Machine-readable description of the authoring dialect, for AI agents.

``gedcom schema`` emits this so an agent can learn the dialect in one call:
the record sections, the enum vocabularies (derived live from the enum
classes, so they never drift), the date grammar, the reference rules, and a
working example. ``gedcom guide`` prints the companion playbook.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from ..enums import (
    AdoptingParent,
    ExidType,
    FamcStatus,
    Medium,
    NameType,
    OrdinanceStatus,
    Pedigree,
    Quality,
    Restriction,
    Role,
    Sex,
)
from .scaffold import scaffold

# Authoring section -> wire record tag (the order matches loader._SECTIONS).
_SECTION_TAGS: dict[str, str] = {
    "submitters": "SUBM",
    "individuals": "INDI",
    "families": "FAM",
    "sources": "SOUR",
    "repositories": "REPO",
    "multimedia": "OBJE",
    "shared_notes": "SNOTE",
}

_ENUMS: tuple[tuple[str, type[StrEnum]], ...] = (
    ("sex", Sex),
    ("restriction", Restriction),
    ("name_type", NameType),
    ("pedigree", Pedigree),
    ("child_status", FamcStatus),
    ("role", Role),
    ("medium", Medium),
    ("quality", Quality),
    ("adopting_parent", AdoptingParent),
    ("ordinance_status", OrdinanceStatus),
)

# Curated field reference per section / shared block. Concise on purpose: the
# agent gets the shape, the enums give exact vocab, and `validate` closes the
# loop. Reference fields name a handle; list fields take one item or a list.
_FIELDS: dict[str, Any] = {
    "individuals": {
        "xref": "handle other records link to (string)",
        "name | names": "name string 'Given /Surname/', or a name block / list of them",
        "sex": "enum: sex",
        "restrictions": "list of enum: restriction",
        "events": "list of event blocks (see _shared.event)",
        "attributes": "list of attribute blocks (event block + required 'value')",
        "non_events": "list of {tag, date (period), date_phrase}",
        "lds_ordinances": "list of {tag, family (ref), detail}",
        "associations": "list of {person (ref), role (enum), phrase, role_phrase}",
        "aliases": "list of {individual (ref), phrase}",
        "submitters | ancestor_interest | descendant_interest": "list of submitter refs",
        "notes": "list of note strings / blocks / shared-note refs (see _shared.note)",
        "sources": "list of source citations (see _shared.citation)",
        "media": "list of media links (see _shared.media_link)",
        "identifiers": "list of {kind: REFN|UID|EXID, value, type}",
        "change_date | creation_date": "{date (exact), time, notes}",
    },
    "families": {
        "xref": "handle",
        "husband | wife": "individual ref (FAMS is derived, never set it)",
        "children": "list of individual refs or child blocks {individual, pedigree, status, *_phrase}; FAMC is derived",
        "events | attributes | non_events": "as individuals; family events accept husband_age/wife_age",
        "sealings": "list of {detail} (spouse sealing, SLGS)",
        "submitters | notes | sources | media | identifiers": "as individuals",
    },
    "sources": {
        "xref": "handle",
        "author | title | abbreviation | publication | text": "text fields",
        "text_mime | text_language": "for the text field",
        "data": "{events: [{events: [tags], date (period), place}], agency, notes}",
        "repository_citations": "list of {repository (ref), call_numbers: [str or {value, medium}]}",
        "notes | media | identifiers": "as individuals",
    },
    "repositories": {
        "xref": "handle",
        "name": "required",
        "address": "address string or block (see _shared.address)",
        "phones | emails | faxes | web_pages": "list of strings",
        "notes | identifiers": "as individuals",
    },
    "multimedia": {
        "xref": "handle",
        "files": "list of {path, form (media type), medium (enum), title, translations: [{path, form}]}",
        "restrictions | notes | sources | identifiers": "as individuals",
    },
    "shared_notes": {
        "xref": "handle",
        "text": "required note text",
        "mime | language": "optional",
        "translations": "list of {text, mime, language}",
        "sources | identifiers": "as individuals",
    },
    "submitters": {
        "xref": "handle",
        "name": "required",
        "address | phones | emails | faxes | web_pages | media | notes | identifiers": "as repositories",
    },
    "_shared": {
        "event": "{tag, occurred (bool, default true when no detail), text (EVEN only), type, + event detail}",
        "event_detail": "{date, time, date_phrase, sort_date, age, husband_age, wife_age, place, address, phones, agency, religion, cause, family_child (ref)+adopting_parent}",
        "name": "{value, type (enum), type_phrase, pieces: {prefix, given, nickname, surname_prefix, surname, suffix}, translations}",
        "place": "string 'City, County, Country', list, or {names, form, language, map: [lat, long], translations}",
        "address": "string, or {value, city, state, postal_code, country}",
        "note": "string, or {text, mime, language, translations}, or {ref: shared-note-handle}",
        "citation": "source-handle string, or {source (ref|VOID), page, data_date, data_texts, event, role (enum), quality (enum), notes, media}",
        "media_link": "multimedia-handle string, or {multimedia (ref), crop: {top, left, height, width}, title}",
    },
}

_DATE_FORMS = [
    "1 JAN 1900",
    "JAN 1900",
    "1900",
    "100 BCE",
    "ABT 1850  /  CAL 1850  /  EST 1850",
    "BET 1900 AND 1910",
    "AFT 1900  /  BEF 1910",
    "FROM 1920 TO 1930  /  FROM 1920  /  TO 1930",
    "JULIAN 1 MAR 1700  /  HEBREW 1 TSH 5700  /  FRENCH_R 1 VEND 1",
]

GUIDE = """\
# Authoring GEDCOM with the `gedcom` CLI

You produce a GEDCOM 7 file from a structured description — you never write
GEDCOM text by hand. Input is a YAML, JSON, or TOML *authoring document*.

## Workflow

1. `gedcom schema`            read the dialect (JSON: sections, enums, dates, example).
2. `gedcom init -f yaml`      get a working starter document to adapt.
3. write your document, then
   `gedcom validate doc.yaml --json`   fix issues until `{"ok": true}`.
4. `gedcom build doc.yaml -o out.ged`  emit the file (`--json` for a structured result).

## Rules

- Records link by handle (their `xref`); references are order-independent;
  `I1` and `@I1@` are equivalent.
- A surname goes between slashes: `John /Smith/`.
- `FAMS`/`FAMC` back-pointers are DERIVED from `families` — never set them.
- Dates use GEDCOM forms (`1 JAN 1900`, `ABT 1850`, `BET a AND b`, `FROM a TO b`);
  native YAML/TOML dates work too.
- Enums accept the member name (`female`) or the spec value (`F`); a `_`-prefixed
  value passes through as an extension.
- Every error is located (path + message); with `--json` it is structured as
  `{"ok": false, "error": {"path": ..., "message": ...}}`.

Run `gedcom schema` for the full field reference and a worked example.
"""


def dialect_schema() -> dict[str, Any]:
    """Return the authoring dialect as a JSON-serializable mapping."""
    return {
        "gedcom_version": "7.0",
        "input_formats": ["yaml", "yml", "json", "toml"],
        "sections": [
            {"key": key, "record": tag, "fields": _FIELDS.get(key, {})}
            for key, tag in _SECTION_TAGS.items()
        ],
        "shared_blocks": _FIELDS["_shared"],
        "enums": {
            name: {
                "accepts": "member name (case-insensitive), spec value, or a _-prefixed extension",
                "values": {member.name.lower(): member.value for member in enum_cls},
            }
            for name, enum_cls in _ENUMS
        },
        "exid_types": {member.name.lower(): member.value for member in ExidType},
        "dates": {
            "forms": _DATE_FORMS,
            "native": "YAML/TOML date and datetime values are accepted",
            "calendars": ["GREGORIAN (default)", "JULIAN", "FRENCH_R", "HEBREW"],
        },
        "references": {
            "by": "handle (a record's xref)",
            "order": "order-independent; a record may reference one defined later",
            "syntax": "the bare handle 'I1' or the wrapped form '@I1@'",
            "void": "use 'VOID' (or omit) where the spec allows an unknown pointer",
        },
        "derived": ["FAM -> INDI FAMS/FAMC back-pointers", "HEAD.SCHMA for used extensions"],
        "workflow": ["schema", "init", "edit", "validate --json", "build -o out.ged"],
        "example": json.loads(scaffold("json")),
    }


def schema_json() -> str:
    """The dialect schema as a pretty-printed JSON string."""
    return json.dumps(dialect_schema(), indent=2)


# --- JSON Schema (Draft 2020-12) for the authoring dialect -----------------
# Editor-time companion to ``validate``: a JSON Schema validates the *parsed*
# document (YAML/JSON/TOML all parse to the same data model), so editors that
# speak ``# yaml-language-server: $schema=`` get autocomplete + inline errors,
# and ``check-jsonschema``/``ajv`` give a fast structural lint. It checks shape,
# property names, and enum vocabularies; ``gedcom validate`` remains the
# authority for cross-reference resolution, date grammar, and cardinality.

_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_IDENTIFIER_KINDS = ("REFN", "UID", "EXID")


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def _enum_schema(enum_cls: type[StrEnum]) -> dict[str, Any]:
    """A field taking an enum: member name, spec value, or ``_``-extension."""
    allowed = sorted({m.name.lower() for m in enum_cls} | {m.value for m in enum_cls})
    return {"anyOf": [{"type": "string", "enum": allowed}, {"type": "string", "pattern": "^_"}]}


def _str_array() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def _obj(props: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        out["required"] = required
    return out


def _defs() -> dict[str, Any]:
    name_block = _obj(
        {
            "value": {"type": "string"},
            "type": _enum_schema(NameType),
            "type_phrase": {"type": "string"},
            "pieces": _obj(
                {
                    "prefix": {"type": "string"},
                    "given": {"type": "string"},
                    "nickname": {"type": "string"},
                    "surname_prefix": {"type": "string"},
                    "surname": {"type": "string"},
                    "suffix": {"type": "string"},
                }
            ),
            "translations": {"type": "array"},
        }
    )
    event = _obj(
        {
            "tag": {"type": "string"},
            "occurred": {"type": "boolean"},
            "text": {"type": "string"},
            "type": {"type": "string"},
            "value": {"type": "string"},  # attribute payload
            "date": {"type": "string"},
            "time": {"type": "string"},
            "date_phrase": {"type": "string"},
            "sort_date": {"type": "string"},
            "age": {"type": "string"},
            "husband_age": {"type": "string"},
            "wife_age": {"type": "string"},
            "place": _ref("place"),
            "address": _ref("address"),
            "phones": _str_array(),
            "agency": {"type": "string"},
            "religion": {"type": "string"},
            "cause": {"type": "string"},
            "family_child": {"type": "string"},
            "adopting_parent": _enum_schema(AdoptingParent),
            "notes": {"type": "array", "items": _ref("note")},
            "sources": {"type": "array", "items": _ref("citation")},
            "media": {"type": "array", "items": _ref("mediaLink")},
        },
        required=["tag"],
    )
    return {
        "handle": {"type": "string"},
        "name": {"anyOf": [{"type": "string"}, name_block]},
        "place": {
            "anyOf": [
                {"type": "string"},
                _str_array(),
                _obj(
                    {
                        "names": {"anyOf": [{"type": "string"}, _str_array()]},
                        "form": {"type": "string"},
                        "language": {"type": "string"},
                        "map": {"type": "array", "items": {"type": "number"}},
                        "translations": {"type": "array"},
                    }
                ),
            ]
        },
        "address": {
            "anyOf": [
                {"type": "string"},
                _obj(
                    {
                        "value": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "postal_code": {"type": "string"},
                        "country": {"type": "string"},
                    }
                ),
            ]
        },
        "note": {
            "anyOf": [
                {"type": "string"},
                _obj(
                    {
                        "text": {"type": "string"},
                        "mime": {"type": "string"},
                        "language": {"type": "string"},
                        "translations": {"type": "array"},
                    }
                ),
                _obj({"ref": {"type": "string"}}),
            ]
        },
        "citation": {
            "anyOf": [
                {"type": "string"},
                _obj(
                    {
                        "source": {"type": "string"},
                        "page": {"type": "string"},
                        "data_date": {"type": "string"},
                        "data_texts": {"type": "array"},
                        "event": {"type": "string"},
                        "role": _enum_schema(Role),
                        "quality": _enum_schema(Quality),
                        "notes": {"type": "array", "items": _ref("note")},
                        "media": {"type": "array", "items": _ref("mediaLink")},
                    }
                ),
            ]
        },
        "mediaLink": {
            "anyOf": [
                {"type": "string"},
                _obj(
                    {
                        "multimedia": {"type": "string"},
                        "crop": _obj(
                            {
                                "top": {"type": "integer"},
                                "left": {"type": "integer"},
                                "height": {"type": "integer"},
                                "width": {"type": "integer"},
                            }
                        ),
                        "title": {"type": "string"},
                    }
                ),
            ]
        },
        "identifier": _obj(
            {
                "kind": {"type": "string", "enum": list(_IDENTIFIER_KINDS)},
                "value": {"type": "string"},
                "type": {"type": "string"},
            },
            required=["kind", "value"],
        ),
        "child": {
            "anyOf": [
                {"type": "string"},
                _obj(
                    {
                        "individual": {"type": "string"},
                        "pedigree": _enum_schema(Pedigree),
                        "status": _enum_schema(FamcStatus),
                        "pedigree_phrase": {"type": "string"},
                        "status_phrase": {"type": "string"},
                    },
                    required=["individual"],
                ),
            ]
        },
        "event": event,
        "nameBlock": name_block,
        "changeDate": _obj(
            {"date": {"type": "string"}, "time": {"type": "string"}, "notes": {"type": "array"}}
        ),
    }


def _record_props(extra: dict[str, Any], *, xref: bool = True) -> dict[str, Any]:
    props: dict[str, Any] = {}
    if xref:
        props["xref"] = _ref("handle")
    props.update(extra)
    return props


def json_schema() -> dict[str, Any]:
    """A JSON Schema (Draft 2020-12) for the authoring dialect.

    Enum vocabularies are pulled live from the enum classes, so the schema
    tracks the library. Record and shared-block shapes are closed
    (``additionalProperties: false``) so a mistyped key is flagged.
    """
    common = {
        "notes": {"type": "array", "items": _ref("note")},
        "sources": {"type": "array", "items": _ref("citation")},
        "media": {"type": "array", "items": _ref("mediaLink")},
        "identifiers": {"type": "array", "items": _ref("identifier")},
    }
    events = {
        "events": {"type": "array", "items": _ref("event")},
        "attributes": {"type": "array", "items": _ref("event")},
        "non_events": {"type": "array"},
    }
    individual = _obj(
        _record_props(
            {
                "name": _ref("name"),
                "names": {"type": "array", "items": _ref("nameBlock")},
                "sex": _enum_schema(Sex),
                "restrictions": {"type": "array", "items": _enum_schema(Restriction)},
                **events,
                "lds_ordinances": {"type": "array"},
                "associations": {"type": "array"},
                "aliases": {"type": "array"},
                "submitters": _str_array(),
                "ancestor_interest": _str_array(),
                "descendant_interest": _str_array(),
                "change_date": _ref("changeDate"),
                "creation_date": _ref("changeDate"),
                **common,
            }
        ),
        required=["xref"],
    )
    family = _obj(
        _record_props(
            {
                "husband": {"type": "string"},
                "wife": {"type": "string"},
                "children": {"type": "array", "items": _ref("child")},
                **events,
                "sealings": {"type": "array"},
                "submitters": _str_array(),
                **common,
            }
        ),
        required=["xref"],
    )
    source = _obj(
        _record_props(
            {
                "author": {"type": "string"},
                "title": {"type": "string"},
                "abbreviation": {"type": "string"},
                "publication": {"type": "string"},
                "text": {"type": "string"},
                "text_mime": {"type": "string"},
                "text_language": {"type": "string"},
                "data": {"type": "object"},
                "repository_citations": {"type": "array"},
                **common,
            }
        ),
        required=["xref"],
    )
    contact = {
        "address": _ref("address"),
        "phones": _str_array(),
        "emails": _str_array(),
        "faxes": _str_array(),
        "web_pages": _str_array(),
    }
    repository = _obj(
        _record_props({"name": {"type": "string"}, **contact, **common}),
        required=["xref", "name"],
    )
    multimedia = _obj(
        _record_props(
            {
                "files": {"type": "array"},
                "restrictions": {"type": "array", "items": _enum_schema(Restriction)},
                **common,
            }
        ),
        required=["xref"],
    )
    shared_note = _obj(
        _record_props(
            {
                "text": {"type": "string"},
                "mime": {"type": "string"},
                "language": {"type": "string"},
                "translations": {"type": "array"},
                **common,
            }
        ),
        required=["xref", "text"],
    )
    submitter = _obj(
        _record_props({"name": {"type": "string"}, **contact, **common}),
        required=["xref", "name"],
    )
    return {
        "$schema": _DRAFT,
        "$id": "https://gedcom.io/authoring-dialect.schema.json",
        "title": "GEDCOM 7 authoring document",
        "description": (
            "Structural schema for the gedcom7 CLI authoring dialect (YAML/JSON/TOML). "
            "Run `gedcom validate` for cross-reference, date-grammar, and cardinality checks."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "header": {"type": "object"},
            "submitters": {"type": "array", "items": submitter},
            "individuals": {"type": "array", "items": individual},
            "families": {"type": "array", "items": family},
            "sources": {"type": "array", "items": source},
            "repositories": {"type": "array", "items": repository},
            "multimedia": {"type": "array", "items": multimedia},
            "shared_notes": {"type": "array", "items": shared_note},
        },
        "$defs": _defs(),
    }


def json_schema_text() -> str:
    """The authoring-dialect JSON Schema as a pretty-printed JSON string."""
    return json.dumps(json_schema(), indent=2)


def schema_text() -> str:
    """A compact human-readable rendering of the dialect schema."""
    schema = dialect_schema()
    lines = ["GEDCOM authoring dialect", "", "Sections (each a list of records):"]
    for section in schema["sections"]:
        lines.append(f"  {section['key']:14} -> {section['record']}")
    lines.append("")
    lines.append("Enums (member name or spec value):")
    for name, info in schema["enums"].items():
        values = ", ".join(f"{k}={v}" for k, v in info["values"].items())
        lines.append(f"  {name}: {values}")
    lines.append("")
    lines.append("Date forms:")
    lines.extend(f"  {form}" for form in schema["dates"]["forms"])
    lines.append("")
    lines.append("Run 'gedcom schema' (JSON) for the full field reference and an example.")
    return "\n".join(lines) + "\n"
