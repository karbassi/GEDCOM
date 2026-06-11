from __future__ import annotations

from gedcom7 import Document, Header, Individual, PersonalName, dumps
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
