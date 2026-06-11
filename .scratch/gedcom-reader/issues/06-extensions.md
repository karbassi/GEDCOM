# 06 — Extensions (SCHMA-declared)

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

Read `HEAD.SCHMA` and decode extension content the inverse of `gedcom.extensions`: map declared extension tags back to their URIs, reconstruct registered and arbitrary **extension structures** wherever they appear, and parse **extension enum values** in enum payloads. An extension tag used without a `SCHMA` declaration is a `ParseError` (strict contract). The `SCHMA` block itself is consumed to build the tag→URI map and is re-emitted identically on write.

## Acceptance criteria

- [ ] A document with a registered extension structure and an arbitrary one round-trips byte-identically, including its auto-emitted `HEAD.SCHMA`.
- [ ] An extension enum value round-trips within its enumeration payload.
- [ ] An undeclared extension tag (no matching `SCHMA` entry) raises `ParseError`.
- [ ] Tests reuse the writer's extension fixtures.
- [ ] `mise run check` is green.

## Blocked by

- 01, 02, 03, 04, 05.
