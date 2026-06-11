# 12 — Source + Source Citation + Repository

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-writer/PRD.md`

## What to build

`Source` (`SOUR` record: `DATA`/`EVEN`, `AUTH`, `TITL`, `ABBR`, `PUBL`, `TEXT`), the `SOURCE_CITATION` block usable from any record (`PAGE`, `DATA`, `EVEN`/`ROLE`, `QUAY`, media, notes; `@VOID@` permitted), `Repository` (`REPO` record with required `NAME`), and `SOURCE_REPOSITORY_CITATION` (`CALN` call numbers, each with optional `MEDI`).

## Acceptance criteria

- [ ] A `Source` and a citation to it from an `Individual` serialize with correct pointers.
- [ ] `QUAY` uses literal `0`–`3`; `ROLE` uses the enum.
- [ ] A `Repository` with `NAME` and a call-number citation serialize; `OBJE`↔`SOUR` and `SNOTE`↔`SOUR` cycles are rejected.
- [ ] Golden + unit tests for a source + citation + repository.

## Blocked by

- #06 Individual + Personal Name
