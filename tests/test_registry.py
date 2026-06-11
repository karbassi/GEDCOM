"""Lock the library to the vendored GEDCOM 7 registry (see ``registry/``).

These tests fail if our hand-curated enums or event payload assumptions ever
drift from the authoritative FamilySearch spec tables.
"""

from __future__ import annotations

import csv
from pathlib import Path

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
from gedcom7.types import _EPOCH_CALENDARS, _MONTHS, Calendar

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


def _registry_exid_uris() -> set[str]:
    with (_REGISTRY / "exid-types.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return {row["uri"] for row in reader}


def test_exid_types_match_registry_exactly() -> None:
    ours = {member.value for member in ExidType}
    assert ours == _registry_exid_uris(), "ExidType drifted from uri/exid-types"


def _registry_calendars() -> dict[str, tuple[list[str], set[str]]]:
    out: dict[str, tuple[list[str], set[str]]] = {}
    with (_REGISTRY / "calendars.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            months = row["months"].split(",")
            epochs = {e for e in row["epochs"].split(",") if e}
            out[row["standard_tag"]] = (months, epochs)
    return out


def test_calendar_months_and_epochs_match_registry() -> None:
    registry = _registry_calendars()
    for calendar in Calendar:
        months, epochs = registry[calendar.value]
        assert _MONTHS[calendar] == months, f"{calendar.value} months drifted"
        permits_epoch = "BCE" in epochs
        assert (calendar in _EPOCH_CALENDARS) == permits_epoch, (
            f"{calendar.value} epoch permission drifted from registry"
        )


def test_packaged_spec_tables_match_vendored_registry() -> None:
    # The runtime copies under the package must stay byte-identical to the
    # vendored registry so validation can't drift from the documented source.
    packaged = _REGISTRY.parents[0] / "src" / "gedcom7" / "_spec"
    for name in ("cardinalities.tsv", "substructures.tsv", "extension-structures.tsv"):
        assert (packaged / name).read_bytes() == (_REGISTRY / name).read_bytes(), (
            f"packaged {name} drifted from registry/{name}"
        )


def test_registered_extensions_match_registry() -> None:
    from collections import defaultdict

    from gedcom7.extensions import registered_extension_uris

    by_tag: dict[str, set[str]] = defaultdict(set)
    with (_REGISTRY / "extension-structures.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            for tag in (row["tags"].split(",") if row["tags"] else []):
                by_tag[tag].add(row["uri"])
    expected = {tag: next(iter(uris)) for tag, uris in by_tag.items() if len(uris) == 1}
    assert registered_extension_uris() == expected


def test_event_tags_have_y_null_payload() -> None:
    # A sampling of standard event tags should carry the [Y|<NULL>] payload.
    payloads: dict[str, str] = {}
    with (_REGISTRY / "payloads.tsv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            payloads[row["structure"].rsplit("/", 1)[-1]] = row["payload"]
    for tag in ("BIRT", "DEAT", "MARR", "ADOP"):
        assert payloads[tag] == "Y|<NULL>"
