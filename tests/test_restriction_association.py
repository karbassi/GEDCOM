from __future__ import annotations

from gedcom import (
    VOID,
    Association,
    Document,
    Individual,
    PersonalName,
    dumps,
)
from gedcom.enums import Restriction, Role


def _indi(name: str, **kw: object) -> Individual:
    return Individual(names=[PersonalName(name)], **kw)  # type: ignore[arg-type]


def test_restriction_list() -> None:
    indi = _indi("X //", restrictions=[Restriction.CONFIDENTIAL, Restriction.LOCKED])
    out = dumps(Document(records=[indi]))
    assert "0 @I1@ INDI\n1 RESN CONFIDENTIAL, LOCKED\n" in out


def test_association_to_individual() -> None:
    godparent = _indi("Gus /Parr/")
    child = _indi("Anne /Allen/", associations=[Association(godparent, Role.GODPARENT)])
    out = dumps(Document(records=[child, godparent]))
    assert "1 ASSO @I2@\n2 ROLE GODP\n" in out


def test_association_void_with_phrase() -> None:
    indi = _indi(
        "X //",
        associations=[Association(VOID, Role.OTHER, phrase="Mr Stockdale", role_phrase="Teacher")],
    )
    out = dumps(Document(records=[indi]))
    assert "1 ASSO @VOID@\n2 PHRASE Mr Stockdale\n2 ROLE OTHER\n3 PHRASE Teacher\n" in out
