"""Lock the library to the vendored GEDCOM 7 registry (see ``registry/``).

These tests fail if our hand-curated enums or event payload assumptions ever
drift from the authoritative FamilySearch spec tables.
"""

from __future__ import annotations

import csv
from pathlib import Path

from gedcom7.enums import (
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

_REGISTRY = Path(__file__).resolve().parents[1] / "registry"

# Our curated enum class → its registry enumset tag.
_ENUM_SETS = {
    "SEX": Sex,
    "RESN": Restriction,
    "MEDI": Medium,
    "PEDI": Pedigree,
    "QUAY": Quality,
    "ROLE": Role,
    "NAME-TYPE": NameType,
    "FAMC-STAT": FamcStatus,
    "ADOP": AdoptingParent,
    "ord-STAT": OrdinanceStatus,
}


def _payload_string(value_uri: str, set_tag: str) -> str:
    """Derive the GEDCOM payload string from a registry value URI."""
    seg = value_uri.rsplit("/", 1)[-1]
    seg = seg.removeprefix("enum-")
    seg = seg.removeprefix(f"{set_tag}-")
    return seg


def _registry_sets() -> dict[str, set[str]]:
    sets: dict[str, set[str]] = {}
    with (_REGISTRY / "enumerationsets.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            set_tag = row["set"].rsplit("/", 1)[-1].removeprefix("enumset-")
            sets.setdefault(set_tag, set()).add(_payload_string(row["value"], set_tag))
    return sets


def test_enums_match_registry_exactly() -> None:
    registry = _registry_sets()
    for set_tag, enum_cls in _ENUM_SETS.items():
        ours = {member.value for member in enum_cls}
        assert ours == registry[set_tag], f"{enum_cls.__name__} drifted from {set_tag}"


def test_every_mapped_set_exists_upstream() -> None:
    registry = _registry_sets()
    for set_tag in _ENUM_SETS:
        assert set_tag in registry, f"enumset {set_tag} no longer in the registry"


def test_event_tags_have_y_null_payload() -> None:
    # A sampling of standard event tags should carry the [Y|<NULL>] payload.
    payloads: dict[str, str] = {}
    with (_REGISTRY / "payloads.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            payloads[row["structure"].rsplit("/", 1)[-1]] = row["payload"]
    for tag in ("BIRT", "DEAT", "MARR", "ADOP"):
        assert payloads[tag] == "Y|<NULL>"
