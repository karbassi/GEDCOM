# 14 — Inline Notes + Shared Note records

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-writer/PRD.md`

## What to build

The two note forms: an inline `NOTE` (Text payload + `MIME`/`LANG`/`TRAN`, where each `TRAN` needs `MIME` and/or `LANG`) and a `SharedNote` (`SNOTE` record carrying its text on the record line, plus `TRAN`), referenced from records via `SNOTE @xref@` pointers. Relies on `CONT` line-splitting (#02).

## Acceptance criteria

- [ ] An inline `NOTE` with a translation, and a `SNOTE` record referenced by pointer, both serialize correctly.
- [ ] A `NOTE.TRAN` / `SNOTE.TRAN` with neither `MIME` nor `LANG` is rejected in strict mode.
- [ ] Multi-line note text uses `CONT` continuation lines.
- [ ] `SNOTE`↔`SOUR` cycles are rejected.
- [ ] Golden + unit tests for inline and shared notes.

## Blocked by

- #02 Line-grammar completeness
- #06 Individual + Personal Name
