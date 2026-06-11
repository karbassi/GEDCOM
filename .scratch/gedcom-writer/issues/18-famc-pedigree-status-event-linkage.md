# 18 — INDI.FAMC pedigree/status + event-level FAMC detail

Status: done
Type: HITL

## Parent

PRD: `.scratch/gedcom-writer/PRD.md` (deferred limitation: `FAMS`/`FAMC` are derived as bare pointers per ADR-0001; per-membership detail is out of v1).

## What to build

Per-membership detail on the child↔family relationship that v1 derives only as bare `FAMC` pointers (ADR-0001):

- `INDI.FAMC.PEDI` (pedigree: birth/adopted/foster/sealing) with `PHRASE`.
- `INDI.FAMC.STAT` (child-to-family status: challenged/disproven/proven) with `PHRASE`.
- Event-level `FAMC` on `BIRT`/`CHR`/`ADOP`, including `ADOP.FAMC.ADOP` (which adopting parent).

Because the `FAMS`/`FAMC` back-pointers are writer-derived rather than stored, this needs a design decision on **where the detail lives** (on the individual's family membership, on the `Family.children` entry, or a dedicated membership object) and whether ADR-0001 needs an amendment. That design call is the HITL portion; implementation follows once the model is decided.

## Acceptance criteria

- [ ] A decision is recorded (ADR amendment or new ADR) for how per-membership `FAMC` detail attaches given derived back-pointers.
- [ ] `INDI.FAMC` can carry `PEDI` and `STAT` (+`PHRASE`), emitted on the derived `FAMC` line block.
- [ ] `BIRT`/`CHR`/`ADOP` events can carry a `FAMC` pointer; `ADOP` can carry `ADOP.FAMC.ADOP` (adopting-parent).
- [ ] Derived `FAMS`/`FAMC` integrity (ADR-0001) still holds — detail augments, never breaks, the derivation.
- [ ] Golden + validation tests for a child with a pedigree/status and an adoption event with a `FAMC`.

## Blocked by

- None - but the design decision (ADR) must land before implementation.
