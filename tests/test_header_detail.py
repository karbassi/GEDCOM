from __future__ import annotations

from gedcom7 import (
    Alias,
    Document,
    Header,
    HeaderSource,
    Individual,
    Note,
    PersonalName,
    Submitter,
    dumps,
)


def test_header_source_dest_lang_note() -> None:
    header = Header(
        source=HeaderSource("MyApp", version="1.2", name="My App", corporation="Acme"),
        destination="OtherApp",
        language="en",
        note=Note("exported for testing"),
    )
    out = dumps(Document(header))
    assert "1 SOUR MyApp\n2 VERS 1.2\n2 NAME My App\n2 CORP Acme\n" in out
    assert "1 DEST OtherApp\n" in out
    assert "1 LANG en\n" in out
    assert "1 NOTE exported for testing\n" in out


def test_individual_alias_anci_desi_subm() -> None:
    subm = Submitter("Researcher")
    alt = Individual(names=[PersonalName("Bob /Smith/")])
    indi = Individual(
        names=[PersonalName("Robert /Smith/")],
        submitters=[subm],
        aliases=[Alias(alt, phrase="same person")],
        ancestor_interest=[subm],
        descendant_interest=[subm],
    )
    out = dumps(Document(records=[indi, alt, subm]))
    assert "1 SUBM @U1@\n" in out
    assert "1 ALIA @I2@\n2 PHRASE same person\n" in out
    assert "1 ANCI @U1@\n" in out
    assert "1 DESI @U1@\n" in out
