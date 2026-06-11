"""The spec-backed cardinality rule set (gedcom7.cardinality)."""

from __future__ import annotations

from gedcom7.cardinality import Rule, build_rules, load_rules

V7 = "https://gedcom.io/terms/v7/"


def test_build_rules_parses_cardinality_tokens() -> None:
    cardinality_rows = [
        {"superstructure": f"{V7}HEAD", "structure": f"{V7}GEDC", "cardinality": "{1:1}"},
        {"superstructure": f"{V7}HEAD", "structure": f"{V7}COPR", "cardinality": "{0:1}"},
        {"superstructure": f"{V7}record-OBJE", "structure": f"{V7}FILE", "cardinality": "{1:M}"},
    ]
    substructure_rows = [
        {"superstructure": "", "tag": "OBJE", "structure": f"{V7}record-OBJE"},
        {"superstructure": f"{V7}HEAD", "tag": "GEDC", "structure": f"{V7}GEDC"},
        {"superstructure": f"{V7}HEAD", "tag": "COPR", "structure": f"{V7}COPR"},
        {"superstructure": f"{V7}record-OBJE", "tag": "FILE", "structure": f"{V7}FILE"},
    ]
    rules = build_rules(cardinality_rows, substructure_rows)

    head = {r.tag: r for r in rules.rules_for(f"{V7}HEAD")}
    assert head["GEDC"] == Rule("GEDC", f"{V7}GEDC", 1, 1)
    assert head["GEDC"].required and head["GEDC"].singular
    assert not head["COPR"].required and head["COPR"].singular

    obje = {r.tag: r for r in rules.rules_for(f"{V7}record-OBJE")}
    assert obje["FILE"].required and not obje["FILE"].singular  # {1:M}
    assert obje["FILE"].maximum is None

    assert "OBJE" in rules.top_level_tags


def test_load_rules_covers_emitted_structures() -> None:
    rules = load_rules()
    # HEAD requires exactly one GEDC.
    gedc = next(r for r in rules.rules_for(f"{V7}HEAD") if r.tag == "GEDC")
    assert gedc.required and gedc.singular
    # An OBJE record requires at least one FILE, repeatable.
    file_rule = next(r for r in rules.rules_for(f"{V7}record-OBJE") if r.tag == "FILE")
    assert file_rule.required and file_rule.maximum is None
    # The level-0 record set is present.
    assert {"INDI", "FAM", "OBJE", "SOUR", "REPO", "SNOTE", "SUBM"} <= rules.top_level_tags
