from __future__ import annotations

from gedcom import (
    Document,
    Individual,
    NamePieces,
    NameTranslation,
    PersonalName,
    dumps,
)
from gedcom.enums import NameType, Sex


def test_minimal_individual_with_name_and_sex() -> None:
    indi = Individual(names=[PersonalName("Joseph /Allen/")], sex=Sex.MALE)
    out = dumps(Document(records=[indi]))
    assert "0 @I1@ INDI\n1 NAME Joseph /Allen/\n1 SEX M\n" in out


def test_name_type_with_phrase() -> None:
    indi = Individual(names=[PersonalName("Maria", type=NameType.MAIDEN, type_phrase="née")])
    out = dumps(Document(records=[indi]))
    assert "1 NAME Maria\n2 TYPE MAIDEN\n3 PHRASE née\n" in out


def test_name_pieces_in_spec_order() -> None:
    name = PersonalName(
        "Lt. Cmndr. Joseph /Allen/ jr.",
        pieces=NamePieces(
            prefix=["Lt. Cmndr."],
            given=["Joseph"],
            surname=["Allen"],
            suffix=["jr."],
        ),
    )
    out = dumps(Document(records=[Individual(names=[name])]))
    assert (
        "1 NAME Lt. Cmndr. Joseph /Allen/ jr.\n"
        "2 NPFX Lt. Cmndr.\n2 GIVN Joseph\n2 SURN Allen\n2 NSFX jr.\n"
    ) in out


def test_name_translation_requires_language() -> None:
    name = PersonalName(
        "Wilhelm /Müller/",
        translations=[NameTranslation("William /Miller/", language="en")],
    )
    out = dumps(Document(records=[Individual(names=[name])]))
    assert "2 TRAN William /Miller/\n3 LANG en\n" in out


def test_individuals_get_sequential_ids() -> None:
    a = Individual(names=[PersonalName("A //")])
    b = Individual(names=[PersonalName("B //")])
    out = dumps(Document(records=[a, b]))
    assert "0 @I1@ INDI" in out
    assert "0 @I2@ INDI" in out


def test_extension_sex_value() -> None:
    indi = Individual(names=[PersonalName("X //")], sex="_NB")
    out = dumps(Document(records=[indi]))
    assert "1 SEX _NB\n" in out
