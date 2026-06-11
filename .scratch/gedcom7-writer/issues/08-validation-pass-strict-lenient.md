# 08 — Validation pass (strict / lenient)

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

The `validation` module: a serialize-time pass enforcing document-level rules — required substructures (`HEAD.GEDC.VERS`, `SUBM.NAME`, and the `INDI`/`FAM` constraints landed so far), xref uniqueness, that every object reference resolves within the `Document`, forbidden `OBJE`↔`SOUR` and `SNOTE`↔`SOUR` cycles, and a deprecation-warning channel. Strict mode raises; lenient mode warns and emits best-effort output (ADR-0002). Later slices extend the rule set with their own constraints.

## Acceptance criteria

- [ ] Strict mode raises a clear, specific error for each violation type; lenient mode emits and surfaces warnings instead.
- [ ] Unresolvable object references and duplicate ids are detected.
- [ ] Forbidden record-cycle detection works for both prohibited pairs.
- [ ] At least one deprecation warning is emitted (e.g. `EXID` without `TYPE`).
- [ ] Unit tests cover each rule in both strict and lenient modes.

## Blocked by

- #07 Family + children birth-order + derived integrity
