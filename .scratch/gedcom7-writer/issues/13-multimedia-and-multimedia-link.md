# 13 — Multimedia + Multimedia Link

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

`Multimedia` (`OBJE` record: `FILE` `{1:M}`, each with a required `FORM` MediaType and optional `MEDI`/`TITL`/`TRAN`) and the `MULTIMEDIA_LINK` block (`OBJE @xref@` with optional `CROP` `TOP`/`LEFT`/`HEIGHT`/`WIDTH` and `TITL`) usable from records.

## Acceptance criteria

- [ ] An `OBJE` with one or more files (each with a `FORM`) serializes; a missing `FILE` or `FILE.FORM` is rejected in strict mode.
- [ ] A multimedia link with crop and title serializes and points correctly.
- [ ] `OBJE`↔`SOUR` cycles are rejected.
- [ ] Golden + unit tests for a multimedia record and a linked image with a crop region.

## Blocked by

- #06 Individual + Personal Name
