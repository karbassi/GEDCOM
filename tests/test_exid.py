"""EXID identifiers using the registered ExidType authority URIs."""

from __future__ import annotations

from gedcom import Document, Identifier, Individual, PersonalName, dumps
from gedcom.enums import ExidType


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_exid_with_exid_type_emits_registry_uri() -> None:
    indi = _indi(
        identifiers=[
            Identifier("EXID", "84128439", type=ExidType.FINDAGRAVE_MEMORIAL_ID),
        ]
    )
    out = dumps(Document(records=[indi]))
    assert "1 EXID 84128439\n2 TYPE https://www.findagrave.com/memorial/\n" in out


def test_exid_with_raw_uri_string_still_works() -> None:
    indi = _indi(identifiers=[Identifier("EXID", "X", type="https://example/auth")])
    out = dumps(Document(records=[indi]))
    assert "1 EXID X\n2 TYPE https://example/auth\n" in out
