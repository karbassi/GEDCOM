# 16 — GEDZIP (.gdz) packaging

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md` (deferred from v1 "Out of Scope": GEDZIP packaging).

## What to build

A packaging path that writes a GEDZIP (`.gdz`) archive: a ZIP container holding the serialized `.ged` as the well-known archive member plus the local media files referenced by `OBJE`/`FILE`, per the GEDCOM 7 GEDZIP specification. Local `FILE` payloads are resolved and stored at archive-relative paths so the references resolve inside the container; remote URLs are left untouched. Exposed alongside the existing `dump`/`dumps` API (e.g. a `dump`-style entry point that targets a `.gdz`).

## Acceptance criteria

- [ ] Produces a valid ZIP with the `.ged` stored at the GEDZIP-specified member path.
- [ ] Local files referenced by `OBJE`/`FILE` are included in the archive; their `FILE` payloads resolve to the archive-relative member paths.
- [ ] Remote (URL) `FILE` references are left as-is and not packaged.
- [ ] A missing local media file is reported via the validation/strict path rather than producing a silently broken archive.
- [ ] Golden test asserting the archive member listing + the rewritten `FILE` paths in the contained `.ged`.

## Blocked by

- None - v1 writer is complete; this layers on top of `dump`.
