# 04 — Cardinality rule set from spec tables

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-registry-alignment/PRD.md`

## What to build

A deep module that ingests the spec's machine-readable cardinality and substructure tables (`cardinalities.tsv`, `substructures.tsv`) into an in-memory rule set: for each superstructure, the permitted substructures with their minimum/maximum occurrences (required vs optional, singular vs repeatable). Pure data-in/data-out, no document dependency — it answers "what are the cardinality rules under structure X?" and is testable in isolation. This is the spec-backed foundation that issue #05 checks documents against.

## Acceptance criteria

- [ ] The module loads `cardinalities.tsv`/`substructures.tsv` into a queryable rule set keyed by superstructure.
- [ ] Each rule exposes the substructure, its minimum occurrences (0/1), and maximum (1/unbounded).
- [ ] A drift/coverage test asserts the rule set covers the structures the writer emits and matches the vendored tables.
- [ ] Unit tests query representative rules (a required-singular, an optional-singular, an optional-repeatable).

## Blocked by

- #01 Vendor registry data + provenance
