# 01 — Payload-type validation

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-payload-conformance/PRD.md`

## What to build

Vendor `payloads.tsv` into the package data (`src/gedcom7/_spec/`) and load it into a structure-URI → payload-datatype map. Extend the existing structure-tree walk (the resolver that powers cardinality validation) to check each emitted line's value against its declared payload type: non-negative-integer payloads must parse as `>= 0`, empty-payload (container) structures must carry no value. Pointer/enum/`Y|<NULL>` types are guaranteed by the model and act only as a backstop — do not duplicate value-level errors the construction layer already raises. Emit `Issue`s into the existing two-tier `validate()` (ADR-0002).

## Acceptance criteria

- [ ] `payloads.tsv` is vendored under `src/gedcom7/_spec/`, byte-identical to `registry/` and drift-guarded.
- [ ] A non-negative-integer payload given a non-integer value (e.g. `Attribute("NCHI", "five")`) is flagged, citing the tag.
- [ ] A container (empty-payload) structure carrying a value is flagged.
- [ ] Strict mode raises `ValidationError`; lenient mode collects — consistent with cardinality.
- [ ] Every existing golden document yields zero payload issues (no false positives).
- [ ] Tests in the style of `tests/test_validation.py` cover a malformed-integer case, an over-filled-container case, and strict-vs-lenient.

## Blocked by

- None - builds on the PRD2 structure resolver (`gedcom7.cardinality`).
