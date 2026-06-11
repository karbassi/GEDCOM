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
    from collections.abc import Iterable


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

    def rules_for(self, superstructure: str) -> tuple[Rule, ...]:
        return self.by_superstructure.get(superstructure, ())


def _parse_cardinality(token: str) -> tuple[int, int | None]:
    """``{0:1}`` -> (0, 1); ``{1:M}`` -> (1, None)."""
    inner = token.strip().removeprefix("{").removesuffix("}")
    lo, hi = inner.split(":")
    return int(lo), (None if hi == "M" else int(hi))


def build_rules(
    cardinality_rows: Iterable[dict[str, str]],
    substructure_rows: Iterable[dict[str, str]],
) -> RuleSet:
    """Build a :class:`RuleSet` from the two tables' rows (pure)."""
    substructure_rows = list(substructure_rows)
    tag_of: dict[tuple[str, str], str] = {
        (r["superstructure"], r["structure"]): r["tag"] for r in substructure_rows
    }
    top_level = frozenset(
        r["tag"] for r in substructure_rows if not r["superstructure"]
    )

    grouped: dict[str, list[Rule]] = {}
    for row in cardinality_rows:
        superstructure, structure = row["superstructure"], row["structure"]
        minimum, maximum = _parse_cardinality(row["cardinality"])
        tag = tag_of[superstructure, structure]
        grouped.setdefault(superstructure, []).append(
            Rule(tag=tag, structure=structure, minimum=minimum, maximum=maximum)
        )
    by_superstructure = {k: tuple(v) for k, v in grouped.items()}
    return RuleSet(by_superstructure=by_superstructure, top_level_tags=top_level)


def _read(name: str) -> list[dict[str, str]]:
    source = resources.files("gedcom7._spec").joinpath(name)
    with resources.as_file(source) as path, path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@cache
def load_rules() -> RuleSet:
    """Load the :class:`RuleSet` from the packaged spec tables (cached)."""
    return build_rules(_read("cardinalities.tsv"), _read("substructures.tsv"))
