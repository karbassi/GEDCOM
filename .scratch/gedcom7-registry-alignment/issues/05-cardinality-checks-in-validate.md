# 05 — Wire cardinality checks into validate()

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-registry-alignment/PRD.md`

## What to build

Use the cardinality rule set (#04) to check a document's serialized structure tree and emit `Issue`s for violations — a missing required substructure or an illegally repeated singular one — each citing the offending structure. Wire this into the existing `validate()` two-tier flow (ADR-0002): strict mode raises, lenient mode collects. The cardinality layer is additive — the existing value-level semantic rules remain.

## Acceptance criteria

- [ ] A missing required substructure (e.g. `OBJE` with no `FILE`) produces an `Issue` citing the structure.
- [ ] An over-repeated singular substructure produces an `Issue`.
- [ ] Strict mode raises `ValidationError`; lenient mode returns the issues — consistent with existing behavior.
- [ ] A valid document produces no cardinality issues (no false positives across the existing golden documents).
- [ ] Tests in the style of `tests/test_validation.py` cover a missing-required case, an over-repeat case, and strict-vs-lenient.

## Blocked by

- #04 Cardinality rule set from spec tables
