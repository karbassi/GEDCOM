# 06 — Individual + Personal Name

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

`Individual` (`INDI`) with one or more Personal Name structures and an optional `SEX`. Each name carries the authoritative `NAME` payload with `/surname/` delimiting, optional name pieces (`NPFX`/`GIVN`/`NICK`/`SPFX`/`SURN`/`NSFX`), a `TYPE` enum, and `TRAN` translations each requiring `LANG`. Uses the `types` (03) and `enums` (04) modules and record xref allocation (05).

## Acceptance criteria

- [ ] An `Individual` with a name and sex emits `0 @I1@ INDI` / `1 NAME Joseph /Allen/` / `1 SEX M` (and name pieces where supplied).
- [ ] Name pieces and `TRAN` (with required `LANG`) serialize correctly under `NAME`.
- [ ] `NAME.TYPE` uses the `NameType` enum.
- [ ] Golden test for a multi-name individual; unit tests for name-piece and translation emission.

## Blocked by

- #03 Data types + calendars
- #04 Typed enums + extension escape hatch
- #05 Submitter record + xref allocation + Header pointer
