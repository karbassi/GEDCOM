# 04 — Remaining records and full header

Status: ready-for-agent
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

Decode the rest of the level-0 record set and the full `HEAD` detail, completing record-level coverage: `OBJE` (Multimedia), `SOUR` (Source), `REPO` (Repository), `SNOTE` (Shared Note), `SUBM` (Submitter), plus every Header substructure the writer emits (`GEDC`/`VERS`, `SOUR`, `DEST`, `DATE`/`TIME`, `SUBM`, `COPR`, `LANG`, `PLAC` form, `NOTE`/`SNOTE`, and the auto-emitted `SCHMA` placeholder handled in slice 06). Pointer payloads on these records (e.g. `SOUR.REPO`, record-level `SUBM`) feed the slice-03 resolver.

## Acceptance criteria

- [ ] A document exercising all seven record types (`HEAD`, `INDI`, `FAM`, `OBJE`, `SOUR`, `REPO`, `SNOTE`, `SUBM`) round-trips byte-identically.
- [ ] Repository citations (`SOUR.REPO` → `Repository`) resolve to object references.
- [ ] Full header detail round-trips, including `DATE`/`TIME` and language/copyright fields.
- [ ] Tests add an all-record-types fixture to the round-trip suite.
- [ ] `mise run check` is green.

## Blocked by

- 01, 02, 03.
