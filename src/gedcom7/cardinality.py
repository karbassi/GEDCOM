"""Spec-backed cardinality rules (§3) derived from the registry tables.

A deep, data-in/data-out module: it ingests the spec's ``cardinalities.tsv``
and ``substructures.tsv`` into an in-memory :class:`RuleSet` answering "what
substructures may appear under structure X, and how many times?". It has no
dependency on the document model — :mod:`gedcom7.validation` consumes it.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import cache
from importlib import resources
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


@dataclass(frozen=True)
class Rule:
    """One permitted substructure of a superstructure.

    ``minimum`` is 0 or 1; ``maximum`` is 1, or ``None`` for unbounded (``M``).
    """

    tag: str
    structure: str
    minimum: int
    maximum: int | None

    @property
    def required(self) -> bool:
        return self.minimum >= 1

    @property
    def singular(self) -> bool:
        return self.maximum == 1


@dataclass(frozen=True)
class RuleSet:
    """Cardinality rules keyed by superstructure URI, plus the level-0 records."""

    by_superstructure: dict[str, tuple[Rule, ...]]
    top_level_tags: frozenset[str]
    # (superstructure URI, tag) -> structure URI; "" superstructure = level 0.
    structure_by_super_tag: dict[tuple[str, str], str]
    # structure URI -> declared payload datatype token (from payloads.tsv).
    payload_by_structure: dict[str, str]

    def rules_for(self, superstructure: str) -> tuple[Rule, ...]:
        return self.by_superstructure.get(superstructure, ())

    def structure_of(self, superstructure: str, tag: str) -> str | None:
        """Resolve the structure URI of ``tag`` under ``superstructure``."""
        return self.structure_by_super_tag.get((superstructure, tag))

    def payload_of(self, structure: str) -> str | None:
        """The declared payload datatype of ``structure``, if known."""
        return self.payload_by_structure.get(structure)


@dataclass(frozen=True)
class Violation:
    """A cardinality breach found while walking an emitted structure tree."""

    structure_tag: str  # the superstructure's tag (e.g. "OBJE")
    child_tag: str  # the offending substructure tag (e.g. "FILE")
    found: int
    minimum: int
    maximum: int | None

    @property
    def message(self) -> str:
        if self.found < self.minimum:
            return (
                f"{self.structure_tag} requires at least {self.minimum} "
                f"{self.child_tag} but has {self.found}"
            )
        return (
            f"{self.structure_tag} allows at most {self.maximum} "
            f"{self.child_tag} but has {self.found}"
        )


@dataclass
class _Frame:
    level: int
    tag: str
    structure: str | None
    counts: dict[str, int]


def check_tree(lines: Iterable[tuple[int, str]], rules: RuleSet) -> Iterator[Violation]:
    """Yield cardinality violations for a ``(level, tag)`` structure stream.

    The stream is in document order. A line's structure is resolved from its
    superstructure + tag; unresolved (extension/unknown) structures and their
    descendants are skipped.
    """

    def finish(frame: _Frame) -> Iterator[Violation]:
        if frame.structure is None:
            return
        for rule in rules.rules_for(frame.structure):
            count = frame.counts.get(rule.tag, 0)
            if count < rule.minimum or (rule.maximum is not None and count > rule.maximum):
                yield Violation(
                    structure_tag=frame.tag,
                    child_tag=rule.tag,
                    found=count,
                    minimum=rule.minimum,
                    maximum=rule.maximum,
                )

    stack: list[_Frame] = []
    for level, tag in lines:
        while stack and stack[-1].level >= level:
            yield from finish(stack.pop())
        parent = stack[-1] if stack else None
        superstructure = "" if parent is None else parent.structure
        if parent is not None and parent.structure is not None:
            parent.counts[tag] = parent.counts.get(tag, 0) + 1
        structure = rules.structure_of(superstructure, tag) if superstructure is not None else None
        stack.append(_Frame(level=level, tag=tag, structure=structure, counts={}))
    while stack:
        yield from finish(stack.pop())


@dataclass(frozen=True)
class PayloadViolation:
    """A line whose value does not match its declared payload datatype."""

    tag: str
    payload: str  # the declared datatype token from payloads.tsv
    value: str | None

    @property
    def message(self) -> str:
        if self.payload == "":
            return f"{self.tag} takes no payload but has a value"
        return f"{self.tag} requires a non-negative integer but has {self.value!r}"


def payload_violations(
    lines: Iterable[tuple[int, str, str | None]], rules: RuleSet
) -> Iterator[PayloadViolation]:
    """Yield payload-type violations for a ``(level, tag, value)`` stream.

    Checks the two datatypes the construction layer does not already guarantee:
    empty-payload (container) structures must carry no value, and
    non-negative-integer structures must hold a non-negative integer. Other
    datatypes (enums, pointers, ``Y|<NULL>``, strings) are model-guaranteed and
    serve only as a backstop. Unresolved (extension) structures are skipped.
    """
    stack: list[tuple[int, str | None]] = []
    for level, tag, value in lines:
        while stack and stack[-1][0] >= level:
            stack.pop()
        superstructure = "" if not stack else stack[-1][1]
        structure = (
            rules.structure_of(superstructure, tag) if superstructure is not None else None
        )
        stack.append((level, structure))
        if structure is None:
            continue
        payload = rules.payload_of(structure)
        if payload is None or value is None:
            continue
        empty_with_value = payload == ""
        bad_integer = "nonNegativeInteger" in payload and not value.isdigit()
        if empty_with_value or bad_integer:
            yield PayloadViolation(tag, payload, value)


def _parse_cardinality(token: str) -> tuple[int, int | None]:
    """``{0:1}`` -> (0, 1); ``{1:M}`` -> (1, None)."""
    inner = token.strip().removeprefix("{").removesuffix("}")
    lo, hi = inner.split(":")
    return int(lo), (None if hi == "M" else int(hi))


def build_rules(
    cardinality_rows: Iterable[dict[str, str]],
    substructure_rows: Iterable[dict[str, str]],
    payload_rows: Iterable[dict[str, str]] = (),
) -> RuleSet:
    """Build a :class:`RuleSet` from the tables' rows (pure)."""
    payload_by_structure = {r["structure"]: r["payload"] for r in payload_rows}
    substructure_rows = list(substructure_rows)
    tag_of: dict[tuple[str, str], str] = {
        (r["superstructure"], r["structure"]): r["tag"] for r in substructure_rows
    }
    structure_by_super_tag: dict[tuple[str, str], str] = {
        (r["superstructure"], r["tag"]): r["structure"] for r in substructure_rows
    }
    top_level = frozenset(r["tag"] for r in substructure_rows if not r["superstructure"])

    grouped: dict[str, list[Rule]] = {}
    for row in cardinality_rows:
        superstructure, structure = row["superstructure"], row["structure"]
        minimum, maximum = _parse_cardinality(row["cardinality"])
        tag = tag_of[superstructure, structure]
        grouped.setdefault(superstructure, []).append(
            Rule(tag=tag, structure=structure, minimum=minimum, maximum=maximum)
        )
    by_superstructure = {k: tuple(v) for k, v in grouped.items()}
    return RuleSet(
        by_superstructure=by_superstructure,
        top_level_tags=top_level,
        structure_by_super_tag=structure_by_super_tag,
        payload_by_structure=payload_by_structure,
    )


def _read(name: str) -> list[dict[str, str]]:
    source = resources.files("gedcom7._spec").joinpath(name)
    with resources.as_file(source) as path, path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@cache
def load_rules() -> RuleSet:
    """Load the :class:`RuleSet` from the packaged spec tables (cached)."""
    return build_rules(
        _read("cardinalities.tsv"),
        _read("substructures.tsv"),
        _read("payloads.tsv"),
    )
