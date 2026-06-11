from __future__ import annotations

import pytest

from gedcom.enums import (
    AdoptingParent,
    Quality,
    Restriction,
    Role,
    Sex,
    enum_list,
    enum_value,
)


def test_sex_values() -> None:
    assert enum_value(Sex.MALE, Sex) == "M"
    assert enum_value(Sex.UNKNOWN, Sex) == "U"


def test_quality_values_are_digit_strings() -> None:
    assert enum_value(Quality.UNRELIABLE, Quality) == "0"
    assert enum_value(Quality.DIRECT, Quality) == "3"


def test_role_tag_values() -> None:
    assert enum_value(Role.GODPARENT, Role) == "GODP"
    assert enum_value(Role.WITNESS, Role) == "WITN"


def test_adopting_parent_values() -> None:
    assert enum_value(AdoptingParent.BOTH, AdoptingParent) == "BOTH"


def test_extension_value_passes_through() -> None:
    assert enum_value("_CUSTOM", Role) == "_CUSTOM"


def test_bare_standard_string_rejected() -> None:
    with pytest.raises(ValueError, match="not a permitted Role value"):
        enum_value("GODP", Role)


def test_enum_list_joins_with_comma_space() -> None:
    out = enum_list([Restriction.CONFIDENTIAL, Restriction.LOCKED], Restriction)
    assert out == "CONFIDENTIAL, LOCKED"


def test_enum_list_allows_extension_value() -> None:
    assert enum_list([Restriction.LOCKED, "_SECRET"], Restriction) == "LOCKED, _SECRET"
