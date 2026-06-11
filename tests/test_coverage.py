"""Structure coverage audit: which standard tags the writer can emit.

Builds a maximal-coverage document, serializes it, and checks the emitted
standard tags against the standard, non-extension structure tags in
``substructures.tsv``. Every gap must be an explicit, documented exclusion.
"""

from __future__ import annotations

import csv
from pathlib import Path

from gedcom7 import (
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
    FileTranslation,
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
    SourceRepositoryCitation,
    Submitter,
    dumps,
)
from gedcom7.enums import (
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
from gedcom7.types import (
    Age,
    CalendarDate,
    DateExact,
    DatePeriod,
    Latitude,
    Longitude,
    Time,
)

_REGISTRY = Path(__file__).resolve().parents[1] / "registry"

# Standard tags with no serialization path, each with a reason (no silent gaps).
EXCLUSIONS = {
    "ADR1": "deprecated address line; intentionally never emitted (ADR-only ADDR)",
    "ADR2": "deprecated address line; intentionally never emitted",
    "ADR3": "deprecated address line; intentionally never emitted",
}

_INDIVIDUAL_EVENTS = [
    "BAPM", "BARM", "BASM", "BLES", "BURI", "CENS", "CHR", "CHRA", "CONF",
    "CREM", "EMIG", "ENGA", "FCOM", "GRAD", "IMMI", "NATU", "ORDN", "PROB",
    "RETI", "WILL",
]  # fmt: skip
_FAMILY_EVENTS = ["ANUL", "CENS", "DIVF", "ENGA", "MARB", "MARC", "MARL", "MARS"]


def _maximal_document() -> Document:
    note = Note(
        "a note",
        mime="text/plain",
        language="en",
        translations=[NoteTranslation("trans", language="fr")],
    )
    snote = SharedNote(
        "shared",
        mime="text/plain",
        language="en",
        translations=[NoteTranslation("t", language="de")],
        identifiers=[Identifier("REFN", "r1", type="x")],
    )
    repo = Repository(
        "Archive",
        address=Address("1 St\nApt", city="C", state="S", postal_code="P", country="Y"),
        phones=["p"], emails=["e"], faxes=["f"], web_pages=["w"], notes=[note],
    )  # fmt: skip
    src = Source(
        author="A", title="T", abbreviation="Ab", publication="Pub", text="Txt",
        text_mime="text/plain", text_language="en",
        data=SourceData(
            events=[
                SourceDataEvent(
                    events=["BIRT"],
                    date=DatePeriod(CalendarDate(1900), CalendarDate(1910)),
                    place=Place(["P"]),
                )
            ],
            agency="ag", notes=[note],
        ),
        repository_citations=[
            SourceRepositoryCitation(repo, call_numbers=[CallNumber("c", medium=Medium.BOOK)])
        ],
        notes=[note], identifiers=[Identifier("UID", "u1")],
    )  # fmt: skip
    obje = Multimedia(
        files=[
            File(
                "p.jpg", "image/jpeg", medium=Medium.PHOTO, title="ti",
                translations=[FileTranslation("p.png", "image/png")],
            )
        ],
        restrictions=[Restriction.CONFIDENTIAL], notes=[note],
        identifiers=[Identifier("EXID", "x", type=ExidType.AFN)],
    )  # fmt: skip
    subm = Submitter(
        "Submitter", address=Address("addr", city="C"), phones=["p"], emails=["e"],
        faxes=["fx"], web_pages=["ww"],
        media_links=[MultimediaLink(obje, crop=Crop(top=1, left=2, height=3, width=4), title="ti")],
        notes=[note], identifiers=[Identifier("REFN", "r")],
    )  # fmt: skip
    detail = EventDetail(
        date=CalendarDate(1900, 1, 1), date_time=Time(1, 2, 3), date_phrase="ph",
        place=Place(
            ["X", "Y"], form=["City", "Country"], language="en",
            translations=[PlaceTranslation(["Z"], "fr")],
            map=Map(Latitude(1.0), Longitude(2.0)),
        ),
        address=Address("a", city="c"), phones=["p"], emails=["e"], faxes=["f"],
        web_pages=["w"], agency="ag", religion="rel", cause="ca",
        age=Age(years=72), age_phrase="abt",
        sort_date=CalendarDate(1850), sort_date_time=Time(1, 2), sort_date_phrase="sp",
    )  # fmt: skip
    fam_detail = EventDetail(
        husband_age=Age(years=30), husband_age_phrase="hp",
        wife_age=Age(years=28, bound=">"), wife_age_phrase="wp",
    )  # fmt: skip
    spouse = Individual(names=[PersonalName("Sp //")])
    child = Individual(names=[PersonalName("Ch //")])
    indi = Individual(
        names=[
            PersonalName(
                "Jo /Doe/",
                type=NameType.BIRTH,
                type_phrase="tp",
                pieces=NamePieces(
                    prefix=["Dr"],
                    given=["Jo"],
                    nickname=["J"],
                    surname_prefix=["van"],
                    surname=["Doe"],
                    suffix=["Jr"],
                ),
                translations=[NameTranslation("Yo /Doe/", "fr", pieces=NamePieces(given=["Yo"]))],
            )
        ],
        sex=Sex.MALE,
        restrictions=[Restriction.LOCKED],
        attributes=[
            Attribute("OCCU", "job", detail=detail),
            Attribute("RESI", "here"),
            Attribute("NCHI", "3"),
            Attribute("NMR", "1"),
            Attribute("DSCR", "tall"),
            Attribute("EDUC", "sch"),
            Attribute("IDNO", "id", type="kind"),
            Attribute("FACT", "f", type="k"),
            Attribute("CAST", "c"),
            Attribute("NATI", "n"),
            Attribute("RELI", "r"),
            Attribute("SSN", "s"),
            Attribute("TITL", "sir"),
            Attribute("PROP", "prop"),
        ],
        events=[
            Event("BIRT", occurred=True, detail=detail),
            Event("DEAT", occurred=True),
            Event("EVEN", text="ev", type="ty"),
            *(Event(t, occurred=True) for t in _INDIVIDUAL_EVENTS),
        ],
        non_events=[
            NonEvent(
                "MARR", date=DatePeriod(CalendarDate(1900), CalendarDate(1910)), date_phrase="np"
            )
        ],
        lds_ordinances=[
            LdsIndividualOrdinance(
                "BAPL",
                detail=LdsOrdinanceDetail(
                    date=CalendarDate(1990, 1, 1),
                    temple="T",
                    place=Place(["P"]),
                    status=OrdinanceStatus.COMPLETED,
                    status_date=DateExact(1990, 1, 2),
                ),
            ),
            LdsIndividualOrdinance("CONL"),
            LdsIndividualOrdinance("ENDL"),
            LdsIndividualOrdinance("INIL"),
        ],
        associations=[
            Association(spouse, role=Role.FRIEND, phrase="ap", role_phrase="rp", notes=[note])
        ],
        submitters=[subm],
        ancestor_interest=[subm],
        descendant_interest=[subm],
        aliases=[Alias(spouse, phrase="aka")],
        notes=[note, snote],
        source_citations=[
            SourceCitation(
                src,
                page="p1",
                data_date=CalendarDate(1900),
                data_texts=["dt"],
                event="BIRT",
                event_phrase="ep",
                role=Role.WITNESS,
                role_phrase="wp",
                quality=Quality.DIRECT,
                notes=[note],
            )
        ],
        media_links=[MultimediaLink(obje)],
        identifiers=[
            Identifier("REFN", "r1", type="t"),
            Identifier("UID", "u"),
            Identifier("EXID", "e", type=ExidType.AFN),
        ],
        extensions=[ExtensionStructure("_DATE", value="2024")],
        change_date=ChangeDate(DateExact(2020, 1, 1), time=Time(1, 2, 3), notes=[note]),
        creation_date=CreationDate(DateExact(2019, 1, 1), time=Time(1, 2)),
    )
    fam = Family(
        husband=indi,
        wife=spouse,
        children=[
            ChildLink(
                child,
                pedigree=Pedigree.BIRTH,
                pedigree_phrase="pp",
                status=FamcStatus.PROVEN,
                status_phrase="sp",
            ),
        ],
        events=[
            Event("MARR", occurred=True, detail=fam_detail),
            Event("DIV", occurred=True),
            *(Event(t, occurred=True) for t in _FAMILY_EVENTS),
        ],
        non_events=[NonEvent("ANUL")],
        sealings=[
            LdsSpouseSealing(detail=LdsOrdinanceDetail(date=CalendarDate(1990, 1, 1), temple="T"))
        ],
        submitters=[subm],
        notes=[note],
        identifiers=[Identifier("REFN", "rf")],
    )
    indi.lds_ordinances.append(LdsIndividualOrdinance("SLGC", family=fam))
    indi.events.append(
        Event("ADOP", detail=EventDetail(family_child=fam, adopting_parent=AdoptingParent.BOTH))
    )
    header = Header(
        source=HeaderSource("Prod", version="1", name="Name", corporation="Corp"),
        destination="DEST",
        date=DateExact(2024, 1, 1),
        time=Time(1, 2, 3),
        submitter=subm,
        language="en",
        place_form=["City", "Country"],
        copyright="(c)",
        note=note,
    )
    return Document(header, records=[subm, indi, spouse, child, fam, src, repo, obje, snote])


def _emitted_tags(text: str) -> set[str]:
    tags: set[str] = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        tags.add(parts[2] if parts[1].startswith("@") else parts[1])
    return tags


def _standard_tags() -> set[str]:
    with (_REGISTRY / "substructures.tsv").open(encoding="utf-8") as handle:
        return {row["tag"] for row in csv.DictReader(handle, delimiter="\t")}


def test_writer_covers_standard_structure_tags() -> None:
    emitted = _emitted_tags(dumps(_maximal_document(), strict=False))
    missing = _standard_tags() - emitted
    assert missing == set(EXCLUSIONS), (
        f"coverage gaps changed: unexpected missing {missing - set(EXCLUSIONS)}, "
        f"newly covered {set(EXCLUSIONS) - missing}"
    )
