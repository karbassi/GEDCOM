# 07 — Family + children birth-order + derived integrity

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

`Family` (`FAM`) linking `Individual`s as `HUSB`/`WIFE` and `CHIL`, with children emitted in birth-chronological order and derived bidirectional integrity: wiring an `Individual` into a `Family` auto-emits the matching `FAMS`/`FAMC` on that individual (ADR-0001). Support a `@VOID@` child placeholder in birth order.

## Acceptance criteria

- [ ] A `Family` emits `HUSB`/`WIFE`/`CHIL` pointers, and the referenced `Individual`s emit matching `FAMS`/`FAMC` automatically.
- [ ] `CHIL` order follows birth order; a `@VOID@` child placeholder is supported.
- [ ] Linking the same individual twice as a child of one family is prevented or flagged.
- [ ] Golden test for a two-parent, multi-child family with back-pointers; unit tests for derived integrity and child ordering.

## Blocked by

- #06 Individual + Personal Name
