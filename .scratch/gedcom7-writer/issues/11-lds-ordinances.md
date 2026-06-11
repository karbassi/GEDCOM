# 11 — LDS ordinances

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

`LDS_INDIVIDUAL_ORDINANCE` (`BAPL`, `CONL`, `ENDL`, `INIL`, `SLGC`) and `LDS_SPOUSE_SEALING` (`SLGS`), each with an `LDS_ORDINANCE_DETAIL` (date, temple, place, `STAT`). `SLGC` requires `FAMC`; `STAT` requires `DATE`; dates must be Gregorian and ≥ 1830. Keep these distinct from the same-spelled events (`BAPL` ≠ `BAPM`, `CONL` ≠ `CONF`).

## Acceptance criteria

- [ ] Each ordinance serializes with its detail; `SLGS` is family-level, the rest individual-level.
- [ ] `SLGC` without `FAMC` and `STAT` without `DATE` are rejected in strict mode.
- [ ] `ord-STAT` enum applicability and deprecated values are respected.
- [ ] Golden + unit tests for a sealing-to-parents (`SLGC`) and an endowment (`ENDL`).

## Blocked by

- #09 Events + attributes + non-events
