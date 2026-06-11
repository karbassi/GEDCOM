"""Record- and substructure-level round-trips (PRD: gedcom-reader, slices 03-06).

Each test builds a model, asserts ``write -> read -> write`` is byte-identical
via the shared harness, and spot-checks that pointers were restored to object
references (not copies).
"""

from __future__ import annotations

import gedcom
from gedcom import (
    VOID,
    Address,
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
    Map,
    Multimedia,
    MultimediaLink,
    NamePieces,
    NonEvent,
    Note,
    PersonalName,
    Place,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceDataEvent,
    SourceRepositoryCitation,
    Submitter,
    read_text,
)
from gedcom.enums import (
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
from test_parse_roundtrip import assert_roundtrips


def test_individual_and_family_roundtrip_with_object_refs() -> None:
    father = Individual(xref_id="I1", names=[PersonalName("John /Smith/")], sex=Sex.MALE)
    mother = Individual(xref_id="I2", names=[PersonalName("Jane /Doe/")], sex=Sex.FEMALE)
    child = Individual(xref_id="I3", names=[PersonalName("Sam /Smith/")])
    family = Family(xref_id="F1", husband=father, wife=mother, children=[child])
    doc = Document(records=[father, mother, child, family])

    assert_roundtrips(doc)

    reparsed = read_text(gedcom.dumps(doc))
    fam = next(r for r in reparsed.records if isinstance(r, Family))
    kids = [r for r in reparsed.records if isinstance(r, Individual)]
    assert fam.husband is kids[0]
    assert fam.children[0] is kids[2]


def test_void_and_dangling_pointers() -> None:
    fam = Family(xref_id="F1", children=[VOID])
    assert_roundtrips(Document(records=[fam]))


def test_child_link_membership_detail_roundtrips() -> None:
    child = Individual(xref_id="I1", names=[PersonalName("Kid /X/")])
    link = ChildLink(child, pedigree=Pedigree.ADOPTED, status=FamcStatus.PROVEN)
    family = Family(xref_id="F1", children=[link])
    assert_roundtrips(Document(records=[child, family]))


def test_events_attributes_and_detail_roundtrip() -> None:
    person = Individual(
        xref_id="I1",
        events=[
            Event(
                "BIRT",
                occurred=True,
                detail=EventDetail(
                    date=CalendarDate(1900, 5, 4),
                    place=Place(
                        ["Boston", "MA", "USA"], map=Map(Latitude(42.36), Longitude(-71.06))
                    ),
                    age=Age(years=0),
                ),
            ),
            Event("DEAT", detail=EventDetail(date=ApproxDate(CalendarDate(1980)))),
            Event("EVEN", text="Won a prize", type="Award"),
        ],
        attributes=[Attribute("OCCU", "Farmer"), Attribute("NCHI", "3")],
        non_events=[NonEvent("MARR", date=DatePeriod(start=CalendarDate(1900)))],
    )
    assert_roundtrips(Document(records=[person]))


def test_full_individual_surface_roundtrips() -> None:
    note = SharedNote(xref_id="N1", text="a shared note")
    source = Source(xref_id="S1", title="A Source")
    media = Multimedia(xref_id="O1", files=[File("photo.jpg", "image/jpeg", medium=Medium.PHOTO)])
    friend = Individual(xref_id="I2", names=[PersonalName("Pat /Pal/")])
    person = Individual(
        xref_id="I1",
        names=[
            PersonalName(
                "Dr. John /Smith/ Jr.",
                type=NameType.BIRTH,
                pieces=NamePieces(
                    prefix=["Dr."], given=["John"], surname=["Smith"], suffix=["Jr."]
                ),
            )
        ],
        sex=Sex.MALE,
        restrictions=[Restriction.CONFIDENTIAL],
        associations=[Association(friend, role=Role.FRIEND)],
        lds_ordinances=[
            LdsIndividualOrdinance(
                "BAPL",
                detail=LdsOrdinanceDetail(
                    date=CalendarDate(1990, 1, 1),
                    temple="SLAKE",
                    status=OrdinanceStatus.COMPLETED,
                    status_date=DateExact(1990, 1, 2),
                ),
            )
        ],
        notes=[Note("inline note"), note],
        identifiers=[Identifier("REFN", "42", type="local"), Identifier("UID", "abc")],
        source_citations=[SourceCitation(source, page="p. 1", quality=Quality.DIRECT)],
        media_links=[MultimediaLink(media, crop=Crop(top=1, left=2), title="portrait")],
        change_date=ChangeDate(DateExact(2020, 6, 1), time=Time(12, 0)),
        creation_date=CreationDate(DateExact(2019, 1, 1)),
    )
    assert_roundtrips(Document(records=[person, friend, note, source, media]))


def test_source_repository_submitter_roundtrip() -> None:
    repo = Repository(
        xref_id="R1",
        name="State Archive",
        address=Address("123 Main St", city="Springfield", country="USA"),
        phones=["555-1234"],
        emails=["info@archive.example"],
    )
    source = Source(
        xref_id="S1",
        author="A. Author",
        title="The Title",
        publication="1999",
        text="some text",
        data=SourceData(
            events=[SourceDataEvent(["BIRT", "DEAT"], date=DatePeriod(start=CalendarDate(1800)))],
            agency="Some Agency",
        ),
        repository_citations=[
            SourceRepositoryCitation(repo, call_numbers=[CallNumber("X.42", medium=Medium.BOOK)])
        ],
    )
    submitter = Submitter(xref_id="U1", name="The Submitter", web_pages=["https://example.com"])
    assert_roundtrips(Document(records=[source, repo, submitter]))


def test_header_detail_roundtrips() -> None:
    submitter = Submitter(xref_id="U1", name="Sub")
    header = Header(
        source=HeaderSource("MyApp", version="1.0", name="My App", corporation="Acme"),
        destination="OtherApp",
        date=DateExact(2024, 3, 15),
        time=Time(9, 30),
        submitter=submitter,
        copyright="(c) 2024",
        language="en",
        place_form=["City", "County", "State", "Country"],
        note=Note("a header note"),
    )
    assert_roundtrips(Document(header=header, records=[submitter]))


def test_extension_structures_roundtrip() -> None:
    person = Individual(
        xref_id="I1",
        extensions=[
            ExtensionStructure("_MYTAG", value="custom", uri="https://example.com/mytag"),
            ExtensionStructure(
                "_PARENT",
                children=(
                    ExtensionStructure("_CHILD", value="x", uri="https://example.com/child"),
                ),
                uri="https://example.com/parent",
            ),
        ],
    )
    assert_roundtrips(Document(records=[person]))


def test_date_range_roundtrips_in_event() -> None:
    person = Individual(
        xref_id="I1",
        events=[
            Event(
                "RESI",
                detail=EventDetail(
                    date=DateRange(after=CalendarDate(1900), before=CalendarDate(1910))
                ),
            )
        ],
    )
    # RESI is an attribute, not an event; use a real event tag instead.
    person.events = [
        Event(
            "CENS",
            detail=EventDetail(date=DateRange(after=CalendarDate(1900), before=CalendarDate(1910))),
        )
    ]
    assert_roundtrips(Document(records=[person]))


def test_julian_and_hebrew_dates_roundtrip() -> None:
    person = Individual(
        xref_id="I1",
        events=[
            Event("BIRT", detail=EventDetail(date=CalendarDate(1700, 3, 1, Calendar.JULIAN))),
            Event("DEAT", detail=EventDetail(date=CalendarDate(5780, 1, calendar=Calendar.HEBREW))),
        ],
    )
    assert_roundtrips(Document(records=[person]))
