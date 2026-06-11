"""The spec-backed cardinality rule set (gedcom.cardinality)."""

from __future__ import annotations

from gedcom.cardinality import (
    Rule,
    build_rules,
    check_tree,
    load_rules,
    payload_violations,
)

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


def test_check_tree_flags_missing_required() -> None:
    rules = load_rules()
    # An OBJE record (level 0) with no FILE substructure.
    violations = list(check_tree([(0, "OBJE")], rules))
    assert any(v.child_tag == "FILE" and v.found == 0 for v in violations)
    assert "OBJE requires at least 1 FILE but has 0" in {v.message for v in violations}


def test_check_tree_flags_over_repeated_singular() -> None:
    rules = load_rules()
    # HEAD permits exactly one GEDC; emit two (plus their required VERS).
    stream = [
        (0, "HEAD"),
        (1, "GEDC"), (2, "VERS"),
        (1, "GEDC"), (2, "VERS"),
    ]  # fmt: skip
    over = [v for v in check_tree(stream, rules) if v.child_tag == "GEDC"]
    assert over and over[0].found == 2 and over[0].maximum == 1
    assert over[0].message == "HEAD allows at most 1 GEDC but has 2"


def test_check_tree_clean_for_valid_minimal_tree() -> None:
    rules = load_rules()
    stream = [(0, "HEAD"), (1, "GEDC"), (2, "VERS"), (0, "TRLR")]
    assert list(check_tree(stream, rules)) == []


def test_check_tree_skips_unresolved_extension_subtree() -> None:
    rules = load_rules()
    # An unknown extension structure and its children are skipped, not flagged.
    stream = [(0, "HEAD"), (1, "GEDC"), (2, "VERS"), (1, "_X"), (2, "_Y")]
    assert list(check_tree(stream, rules)) == []


def test_payload_violations_flags_non_integer_nchi() -> None:
    rules = load_rules()
    # INDI with an NCHI attribute carrying a non-integer payload.
    stream = [(0, "INDI", None), (1, "NCHI", "five")]
    breaches = list(payload_violations(stream, rules))
    assert any(b.tag == "NCHI" for b in breaches)
    assert "NCHI requires a non-negative integer but has 'five'" in {b.message for b in breaches}


def test_payload_violations_accepts_integer_nchi() -> None:
    rules = load_rules()
    assert list(payload_violations([(0, "INDI", None), (1, "NCHI", "3")], rules)) == []


def test_payload_violations_flags_value_on_container() -> None:
    rules = load_rules()
    # HEAD is an empty-payload (container) structure; a value is a violation.
    breaches = list(payload_violations([(0, "HEAD", "oops")], rules))
    assert any(b.tag == "HEAD" and "takes no payload" in b.message for b in breaches)


def test_payload_violations_skips_unresolved_extension() -> None:
    rules = load_rules()
    assert list(payload_violations([(0, "HEAD", None), (1, "_X", "anything")], rules)) == []
