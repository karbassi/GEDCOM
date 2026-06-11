from __future__ import annotations

import warnings

from gedcom import (
    Address,
    Document,
    Event,
    EventDetail,
    Header,
    Identifier,
    Individual,
    Map,
    PersonalName,
    Place,
    PlaceTranslation,
    Submitter,
    dumps,
)
from gedcom.types import Latitude, Longitude


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_place_with_form_and_map() -> None:
    place = Place(
        names=["Cove", "Cache", "Utah", "USA"],
        form=["City", "County", "State", "Country"],
        map=Map(Latitude(41.916), Longitude(-111.804)),
    )
    indi = _indi(events=[Event("BIRT", detail=EventDetail(place=place))])
    out = dumps(Document(records=[indi]))
    assert "1 BIRT\n2 PLAC Cove, Cache, Utah, USA\n3 FORM City, County, State, Country\n" in out
    assert "3 MAP\n4 LATI N41.916\n4 LONG W111.804\n" in out


def test_place_translation_requires_language() -> None:
    place = Place(names=["Roma"], translations=[PlaceTranslation(["Rome"], "en")])
    indi = _indi(events=[Event("BIRT", detail=EventDetail(place=place))])
    out = dumps(Document(records=[indi]))
    assert "2 PLAC Roma\n3 TRAN Rome\n4 LANG en\n" in out


def test_address_on_submitter() -> None:
    subm = Submitter("Ali", address=Address("1 Main St\nApt 2", city="Boston", country="USA"))
    out = dumps(Document(records=[subm]))
    assert "1 ADDR 1 Main St\n2 CONT Apt 2\n2 CITY Boston\n2 CTRY USA\n" in out


def test_header_place_form() -> None:
    out = dumps(Document(Header(place_form=["City", "County", "State", "Country"])))
    assert "1 PLAC\n2 FORM City, County, State, Country\n" in out


def test_identifiers() -> None:
    indi = _indi(
        identifiers=[
            Identifier("REFN", "X1", type="user-ref"),
            Identifier("UID", "urn:uuid:1234"),
            Identifier("EXID", "https://ex/123", type="https://ex/authority"),
        ]
    )
    out = dumps(Document(records=[indi]))
    assert "1 REFN X1\n2 TYPE user-ref\n" in out
    assert "1 UID urn:uuid:1234\n" in out
    assert "1 EXID https://ex/123\n2 TYPE https://ex/authority\n" in out


def test_exid_without_type_warns_in_lenient_mode() -> None:
    indi = _indi(identifiers=[Identifier("EXID", "https://ex/123")])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dumps(Document(records=[indi]), strict=False)
    assert any("EXID without a TYPE is deprecated" in str(w.message) for w in caught)
