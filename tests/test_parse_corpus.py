"""Full-corpus round-trip property (PRD: gedcom-reader, slice 08).

A broad corpus spanning every record type, substructure block, calendar, and
extension is run through both oracles: the text oracle (``write -> read ->
write`` is byte-identical) and the model oracle (``read(write(doc))`` equals
``doc`` structurally, ignoring transient xref ids — here pinned, so equality
holds directly).
"""

from __future__ import annotations

import dataclasses

import pytest

import gedcom
from gedcom import (
    VOID,
    Address,
    Alias,
    Association,
    Attribute,
    CallNumber,
    ChangeDate,
    ChildLink,
    CreationDate,
    Crop,
    Document,
    Event,
    EventDetail,
    ExtensionStructure,
    Family,
    File,
    Header,
    HeaderSource,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsOrdinanceDetail,
    LdsSpouseSealing,
    Map,
    Multimedia,
    MultimediaLink,
    NamePieces,
    NameTranslation,
    NonEvent,
    Note,
    NoteTranslation,
    PersonalName,
    Place,
    PlaceTranslation,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceDataEvent,
    Submitter,
    read_text,
)
from gedcom.enums import (
    AdoptingParent,
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
from gedcom.types import (
    Age,
    ApproxDate,
    Calendar,
    CalendarDate,
    DateExact,
    DatePeriod,
    DateRange,
    Latitude,
    Longitude,
    Time,
)


def _empty() -> Document:
    return Document()


def _header_full() -> Document:
    subm = Submitter(xref_id="U1", name="Sub")
    return Document(
        header=Header(
            source=HeaderSource("App", version="2", name="The App", corporation="Co"),
            destination="Dest",
            date=DateExact(2024, 1, 1),
            time=Time(0, 0, 1),
            submitter=subm,
            copyright="(c)",
            language="en-US",
            place_form=["City", "Country"],
            note=Note("header note", language="en"),
        ),
        records=[subm],
    )


def _family_tree() -> Document:
    dad = Individual(xref_id="I1", names=[PersonalName("Bob /Lee/")], sex=Sex.MALE)
    mom = Individual(xref_id="I2", names=[PersonalName("Sue /Lee/")], sex=Sex.FEMALE)
    kid = Individual(xref_id="I3", names=[PersonalName("Tim /Lee/")])
    fam = Family(
        xref_id="F1",
        husband=dad,
        wife=mom,
        children=[ChildLink(kid, pedigree=Pedigree.BIRTH, status=FamcStatus.PROVEN), VOID],
        events=[Event("MARR", occurred=True, detail=EventDetail(date=CalendarDate(1950, 6, 1)))],
    )
    return Document(records=[dad, mom, kid, fam])


def _names_and_translations() -> Document:
    person = Individual(
        xref_id="I1",
        names=[
            PersonalName(
                "José /García/",
                type=NameType.BIRTH,
                pieces=NamePieces(given=["José"], surname=["García"]),
                translations=[
                    NameTranslation(
                        "Joseph /Garcia/", language="en", pieces=NamePieces(given=["Joseph"])
                    )
                ],
            )
        ],
    )
    return Document(records=[person])


def _all_calendars() -> Document:
    return Document(
        records=[
            Individual(
                xref_id="I1",
                events=[
                    Event("BIRT", detail=EventDetail(date=CalendarDate(1900, 5, 4))),
                    Event(
                        "DEAT", detail=EventDetail(date=CalendarDate(1700, 3, 1, Calendar.JULIAN))
                    ),
                    Event(
                        "BAPM",
                        detail=EventDetail(date=CalendarDate(8, 2, calendar=Calendar.FRENCH_R)),
                    ),
                    Event(
                        "BURI",
                        detail=EventDetail(date=CalendarDate(5780, 1, calendar=Calendar.HEBREW)),
                    ),
                    Event("CHR", detail=EventDetail(date=CalendarDate(44, bce=True))),
                ],
            )
        ]
    )


def _date_forms() -> Document:
    return Document(
        records=[
            Individual(
                xref_id="I1",
                events=[
                    Event("CENS", detail=EventDetail(date=ApproxDate(CalendarDate(1880), "EST"))),
                    Event(
                        "EMIG",
                        detail=EventDetail(
                            date=DateRange(after=CalendarDate(1850), before=CalendarDate(1860))
                        ),
                    ),
                    Event(
                        "IMMI",
                        detail=EventDetail(date=DatePeriod(CalendarDate(1851), CalendarDate(1852))),
                    ),
                ],
                non_events=[
                    NonEvent("NATU", date=DatePeriod(start=CalendarDate(1840)), date_phrase="never")
                ],
            )
        ]
    )


def _attributes_and_detail() -> Document:
    return Document(
        records=[
            Individual(
                xref_id="I1",
                attributes=[
                    Attribute(
                        "OCCU", "Baker", detail=EventDetail(agency="Guild", age=Age(years=40))
                    ),
                    Attribute("NCHI", "5"),
                    Attribute("IDNO", "X9", type="badge"),
                ],
            )
        ]
    )


def _event_famc_adoption() -> Document:
    parents = Family(xref_id="F1")
    child = Individual(
        xref_id="I1",
        events=[
            Event(
                "ADOP",
                occurred=True,
                detail=EventDetail(
                    family_child=parents,
                    adopting_parent=AdoptingParent.BOTH,
                    adopting_parent_phrase="both parents",
                ),
            )
        ],
    )
    return Document(records=[child, parents])


def _lds() -> Document:
    spouse_a = Individual(xref_id="I1")
    spouse_b = Individual(xref_id="I2")
    parents = Family(xref_id="F1", husband=spouse_a, wife=spouse_b)
    child = Individual(
        xref_id="I3",
        lds_ordinances=[
            LdsIndividualOrdinance(
                "SLGC",
                detail=LdsOrdinanceDetail(
                    date=CalendarDate(1990, 1, 1),
                    temple="SLAKE",
                    status=OrdinanceStatus.COMPLETED,
                    status_date=DateExact(1990, 1, 2),
                    status_time=Time(10, 0),
                ),
                family=parents,
            )
        ],
    )
    fam = Family(
        xref_id="F2",
        sealings=[
            LdsSpouseSealing(
                detail=LdsOrdinanceDetail(date=CalendarDate(1985, 5, 5), temple="LOGAN")
            )
        ],
    )
    return Document(records=[spouse_a, spouse_b, child, parents, fam])


def _sources_and_repos() -> Document:
    repo = Repository(
        xref_id="R1", name="Archive", address=Address("1 St", city="Town"), phones=["555"]
    )
    src = Source(
        xref_id="S1",
        author="Auth",
        title="Title",
        abbreviation="T",
        publication="Pub",
        text="body",
        text_mime="text/plain",
        text_language="en",
        data=SourceData(
            events=[
                SourceDataEvent(
                    ["BIRT"],
                    date=DatePeriod(CalendarDate(1800), CalendarDate(1850)),
                    place=Place(["Town"]),
                )
            ],
            agency="Agency",
            notes=[Note("data note")],
        ),
    )
    from gedcom import SourceRepositoryCitation

    src.repository_citations = [
        SourceRepositoryCitation(
            repo, call_numbers=[CallNumber("A.1", medium=Medium.BOOK), CallNumber("B.2")]
        )
    ]
    person = Individual(
        xref_id="I1",
        source_citations=[
            SourceCitation(
                src,
                page="p.1",
                data_date=CalendarDate(1801),
                data_texts=["t1", "t2"],
                event="BIRT",
                event_phrase="the birth",
                role=Role.WITNESS,
                quality=Quality.DIRECT,
                notes=[Note("cite note")],
            ),
            SourceCitation(VOID, page="whole source"),
        ],
    )
    return Document(records=[person, src, repo])


def _multimedia_and_notes() -> Document:
    snote = SharedNote(
        xref_id="N1",
        text="shared",
        mime="text/plain",
        language="en",
        translations=[NoteTranslation("partagé", language="fr")],
    )
    media = Multimedia(
        xref_id="O1",
        files=[
            File("a.jpg", "image/jpeg", medium=Medium.PHOTO, title="A"),
            File("b.png", "image/png"),
        ],
        restrictions=[Restriction.CONFIDENTIAL],
        notes=[Note("media note", translations=[NoteTranslation("note", language="fr")])],
    )
    person = Individual(
        xref_id="I1",
        notes=[Note("inline"), snote],
        media_links=[MultimediaLink(media, crop=Crop(top=1, left=2, height=3, width=4), title="t")],
        identifiers=[
            Identifier("REFN", "1", type="local"),
            Identifier("UID", "u"),
            Identifier("EXID", "e", type="http://x"),
        ],
    )
    return Document(records=[person, media, snote])


def _associations_and_aliases() -> Document:
    other = Individual(xref_id="I2", names=[PersonalName("Al /Pal/")])
    person = Individual(
        xref_id="I1",
        associations=[
            Association(other, role=Role.FRIEND, phrase="best friend", role_phrase="the friend"),
            Association(VOID, role=Role.OTHER, phrase="unknown person"),
        ],
        aliases=[Alias(other, phrase="also known")],
    )
    return Document(records=[person, other])


def _places_full() -> Document:
    return Document(
        records=[
            Individual(
                xref_id="I1",
                events=[
                    Event(
                        "BIRT",
                        detail=EventDetail(
                            place=Place(
                                ["Paris", "France"],
                                form=["City", "Country"],
                                language="en",
                                translations=[
                                    PlaceTranslation(["Parizo", "Francio"], language="eo")
                                ],
                                map=Map(Latitude(48.8566), Longitude(2.3522)),
                            ),
                            address=Address("1 Rue", city="Paris", country="France"),
                            phones=["1"],
                            emails=["a@b.c"],
                        ),
                    )
                ],
            )
        ]
    )


def _extensions() -> Document:
    return Document(
        header=Header(schema={"_FLAG": "https://example.com/flag"}),
        records=[
            Individual(
                xref_id="I1",
                extensions=[
                    ExtensionStructure("_X", value="v", uri="https://example.com/x"),
                    ExtensionStructure(
                        "_Y",
                        children=(
                            ExtensionStructure("_Z", value="z", uri="https://example.com/z"),
                        ),
                        uri="https://example.com/y",
                    ),
                ],
            )
        ],
    )


def _metadata() -> Document:
    note = SharedNote(xref_id="N1", text="n")
    person = Individual(
        xref_id="I1",
        change_date=ChangeDate(
            DateExact(2020, 1, 1), time=Time(1, 2, 3), notes=[Note("changed"), note]
        ),
        creation_date=CreationDate(DateExact(2019, 1, 1), time=Time(4, 5)),
    )
    return Document(records=[person, note])


CORPUS = {
    "empty": _empty(),
    "header_full": _header_full(),
    "family_tree": _family_tree(),
    "names_and_translations": _names_and_translations(),
    "all_calendars": _all_calendars(),
    "date_forms": _date_forms(),
    "attributes_and_detail": _attributes_and_detail(),
    "event_famc_adoption": _event_famc_adoption(),
    "lds": _lds(),
    "sources_and_repos": _sources_and_repos(),
    "multimedia_and_notes": _multimedia_and_notes(),
    "associations_and_aliases": _associations_and_aliases(),
    "places_full": _places_full(),
    "extensions": _extensions(),
    "metadata": _metadata(),
}


@pytest.mark.parametrize("name", list(CORPUS))
def test_text_oracle(name: str) -> None:
    text = gedcom.dumps(CORPUS[name])
    assert gedcom.dumps(read_text(text)) == text


@pytest.mark.parametrize("name", list(CORPUS))
def test_model_oracle(name: str) -> None:
    # All corpus documents pin their xref ids, so structural equality holds
    # directly. header.schema is a serialization-derived map (the writer emits
    # only the SCHMA entries actually used), so — like transient xref ids — it
    # is not a faithfully-preserved model field and is excluded here; the text
    # oracle covers its on-the-wire fidelity.
    doc = CORPUS[name]
    reparsed = read_text(gedcom.dumps(doc))
    assert reparsed.records == doc.records
    assert dataclasses.replace(reparsed.header, schema={}) == dataclasses.replace(
        doc.header, schema={}
    )
