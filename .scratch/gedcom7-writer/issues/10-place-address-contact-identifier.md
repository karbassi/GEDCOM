# 10 — Place / Address / contact / identifier structures

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

The shared location and identifier substructure blocks: `PLACE_STRUCTURE` (comma-list smallest→largest, `FORM` with `HEAD.PLAC.FORM` fallback, `LANG`, `TRAN` requiring `LANG`, `MAP` requiring both `LATI`+`LONG`, `EXID`), `ADDRESS_STRUCTURE` (`ADDR` payload required; structured subfields; no `ADR1/2/3`), contact details (`PHON`/`EMAIL`/`FAX`/`WWW`), and `IDENTIFIER_STRUCTURE` (`REFN`/`UID`/`EXID` with `TYPE`).

## Acceptance criteria

- [ ] Places serialize smallest→largest with `FORM`; missing elements left blank; `MAP` requires both coordinates.
- [ ] `ADDR` payload is always emitted; `ADR1/2/3` are never emitted.
- [ ] `EXID` without `TYPE` raises a deprecation warning.
- [ ] Identifier structures serialize correctly under records.
- [ ] Golden + unit tests covering a place (with map), an address, and identifiers.

## Blocked by

- #09 Events + attributes + non-events
