# 07 — GEDZIP (.gdz) reading

Status: ready-for-agent
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

`read_path(p)` dispatches on extension: `.ged` reads text directly; `.gdz` reads the GEDZIP package — the inverse of `gedcom.gedzip`. Open the zip, read the GEDCOM payload member, parse it via the text path, and expose bundled media members consistent with how the writer packaged them. Guard the unzip against path-traversal entries (members escaping the archive root) and zip-bomb entries (implausible decompressed size / ratio); both raise `ParseError`. This is the only slice that touches untrusted-shaped bytes, so the guards are mandatory even within the "our own output" promise.

## Acceptance criteria

- [ ] A `.gdz` written by the library round-trips: `read_path(p)` then re-write produces a byte-identical archive payload.
- [ ] Bundled media members are recovered and associated with their `Multimedia` records.
- [ ] A crafted path-traversal member (`../…`) raises `ParseError`.
- [ ] A zip-bomb-shaped member (excessive decompressed ratio) raises `ParseError`.
- [ ] `read_path` selects the text vs GEDZIP path by extension and is covered by tests for both.
- [ ] `mise run check` is green.

## Blocked by

- 01, 02, 03, 04, 05 (06 not strictly required but expected).
