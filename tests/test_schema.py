from __future__ import annotations

import json

import pytest

from gedcom7 import Document, Header, Individual, PersonalName, dumps
from gedcom7.cli.scaffold import scaffold
from gedcom7.cli.schema import dialect_schema, json_schema, json_schema_text
from gedcom7.enums import Sex


def test_extension_enum_value_auto_emits_schema() -> None:
    header = Header(schema={"_NB": "https://example.org/terms/non-binary"})
    indi = Individual(names=[PersonalName("X //")], sex="_NB")
    out = dumps(Document(header, records=[indi]))
    assert (
        "0 HEAD\n1 GEDC\n2 VERS 7.0\n1 SCHMA\n2 TAG _NB https://example.org/terms/non-binary\n"
    ) in out
    assert "1 SEX _NB\n" in out


def test_no_schema_when_no_extensions_used() -> None:
    header = Header(schema={"_NB": "https://example.org/terms/non-binary"})
    indi = Individual(names=[PersonalName("X //")], sex=Sex.MALE)
    out = dumps(Document(header, records=[indi]))
    assert "SCHMA" not in out


def test_no_schema_block_by_default() -> None:
    assert "SCHMA" not in dumps(Document())


def test_multiple_extensions_sorted() -> None:
    header = Header(schema={"_ZED": "https://ex/z", "_ABLE": "https://ex/a"})
    indi = Individual(names=[PersonalName("X //")], sex="_ZED", attributes=[])
    # only _ZED is used here
    out = dumps(Document(header, records=[indi]))
    assert "2 TAG _ZED https://ex/z\n" in out
    assert "_ABLE" not in out


def test_json_schema_shape() -> None:
    schema = json_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    props = schema["properties"]
    for key in ("header", "submitters", "individuals", "families", "sources",
                "repositories", "multimedia", "shared_notes"):
        assert key in props
    # the dialect sections (minus the header pseudo-record) match the schema command
    assert set(props) - {"header"} == {s["key"] for s in dialect_schema()["sections"]}
    assert "$defs" in schema


def test_json_schema_enums_are_live() -> None:
    sex = json_schema()["properties"]["individuals"]["items"]["properties"]["sex"]
    allowed = sex["anyOf"][0]["enum"]
    assert "male" in allowed and "F" in allowed  # member name and spec value both accepted


def test_json_schema_required_fields() -> None:
    schema = json_schema()
    items = schema["properties"]
    assert items["individuals"]["items"]["required"] == ["xref"]
    assert items["submitters"]["items"]["required"] == ["xref", "name"]
    assert items["shared_notes"]["items"]["required"] == ["xref", "text"]
    ident = schema["$defs"]["identifier"]
    assert ident["required"] == ["kind", "value"]


def test_json_schema_text_is_valid_json() -> None:
    assert json.loads(json_schema_text())["title"] == "GEDCOM 7 authoring document"


def test_json_schema_is_a_valid_metaschema_and_accepts_the_scaffold() -> None:
    jsonschema = pytest.importorskip("jsonschema")  # optional; skipped if absent
    schema = json_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(json.loads(scaffold("json")), schema)
