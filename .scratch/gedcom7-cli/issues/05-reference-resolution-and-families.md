# Reference resolution + families

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

Handle-based reference resolution (two-pass: construct + register by `xref`, then wire object references) and `families`: `husband`/`wife`/`children` (including `ChildLink` membership detail), family events/attributes. References are order-independent and tolerate a surrounding `@…@`. Derived `FAMS`/`FAMC` come from the writer (ADR-0001). Dangling or wrong-typed references raise a located error.

## Acceptance criteria

- [ ] A family referencing individuals by handle emits `HUSB`/`WIFE`/`CHIL` and the derived `FAMS`/`FAMC` on the individuals.
- [ ] Forward references (family before the referenced individual) resolve.
- [ ] `children` entries may carry pedigree/status detail (ChildLink).
- [ ] A reference to a missing or wrong-typed handle raises a located error.

## Blocked by

- 04 (loader tracer)
