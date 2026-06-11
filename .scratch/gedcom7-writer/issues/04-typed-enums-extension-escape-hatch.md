# 04 — Typed enums + extension escape hatch

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

The `enums` module: one Python enum per enumeration set (`Sex`, `Resn` [list], `Medi`, `Pedi`, `Quay`, `Role`, `NameType`, `FamcStat`, `Adop`, `OrdStat`, plus the EVEN/EVENATTR value sets) emitting the exact spec strings; accept a `_`-prefixed extension string anywhere extension enum values are permitted; validate membership; and disambiguate tag/URI collisions by superstructure where relevant. Support an accompanying `PHRASE` for `OTHER` at the structure level (consumed by later slices).

## Acceptance criteria

- [ ] Each enum emits the exact permitted strings (e.g. `Sex.MALE`→`M`; `Quay` values are literal `0`–`3`).
- [ ] `Resn` serializes as a comma-space list (e.g. `CONFIDENTIAL, LOCKED`).
- [ ] A `_`-prefixed extension value is accepted and passed through where the spec allows; a non-permitted standard string is rejected.
- [ ] Tag/URI collisions documented and disambiguated by containing structure.
- [ ] Unit tests cover each enum set and the extension passthrough/rejection.

## Blocked by

- #01 Walking skeleton: minimal valid document
