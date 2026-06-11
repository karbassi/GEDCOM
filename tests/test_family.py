from __future__ import annotations

from gedcom7 import VOID, Document, Family, Individual, PersonalName, dumps


def _indi(name: str) -> Individual:
    return Individual(names=[PersonalName(name)])


def test_family_links_and_derived_back_pointers() -> None:
    father = _indi("Joseph /Allen/")
    mother = _indi("Mary /Smith/")
    child = _indi("Anne /Allen/")
    fam = Family(husband=father, wife=mother, children=[child])
    out = dumps(Document(records=[father, mother, child, fam]))

    # Family record points at its members...
    assert "0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 CHIL @I3@\n" in out
    # ...and the members carry derived back-pointers.
    assert "0 @I1@ INDI\n1 NAME Joseph /Allen/\n1 FAMS @F1@\n" in out
    assert "0 @I3@ INDI\n1 NAME Anne /Allen/\n1 FAMC @F1@\n" in out


def test_children_keep_birth_order() -> None:
    a, b, c = _indi("A //"), _indi("B //"), _indi("C //")
    fam = Family(children=[a, b, c])
    out = dumps(Document(records=[a, b, c, fam]))
    chil_block = out[out.index("0 @F1@ FAM") :]
    assert "1 CHIL @I1@\n1 CHIL @I2@\n1 CHIL @I3@\n" in chil_block


def test_void_child_placeholder() -> None:
    a = _indi("A //")
    fam = Family(children=[VOID, a])
    out = dumps(Document(records=[a, fam]))
    assert "1 CHIL @VOID@\n1 CHIL @I1@\n" in out


def test_individual_in_two_families_gets_both_links() -> None:
    person = _indi("P //")
    spouse = _indi("S //")
    parents = Family(children=[person])
    own = Family(husband=person, wife=spouse)
    out = dumps(Document(records=[person, spouse, parents, own]))
    # parents = @F1@, own = @F2@
    assert "0 @I1@ INDI\n1 NAME P //\n1 FAMC @F1@\n1 FAMS @F2@\n" in out
