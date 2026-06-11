# 01 — Vendor EXID/calendar/month/extension registry data + provenance

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-registry-alignment/PRD.md`

## What to build

Extend `registry/` with the `GEDCOM-registries` data the rest of this PRD drift-locks against: the EXID type definitions (`uri/exid-types`), the four standard calendars (`calendar/standard`), the months (`month/standard`), and the registered extension structures (`structure/extension`). Record the exact upstream `GEDCOM-registries` commit in `registry/README.md` alongside the existing `familysearch/GEDCOM` provenance. Tests must read the vendored copy offline — no network access at test time.

## Acceptance criteria

- [ ] EXID type, calendar, month, and registered-extension data is vendored under `registry/` in a form the drift tests can read deterministically.
- [ ] `registry/README.md` pins the `GEDCOM-registries` commit SHA and lists what was vendored from it.
- [ ] No test in the suite makes a network call to obtain registry data.

## Blocked by

- None - can start immediately.
