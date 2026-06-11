# 05 — Substructure blocks

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

`parse/_substructures.py` — the inverse of `serialize/_substructures.py`, the bulk of the decoder. Decode every reusable substructure block the writer emits: personal names (with translations and name pieces), events and event detail, attributes, non-events, places (with form/translations/coordinates), addresses, source citations and repository citations, multimedia links (with crop/title), inline notes and note translations, identifiers, associations, restrictions, LDS individual ordinances and spouse sealings, and change/creation dates. Each decoder mirrors its encoder so the two read side by side.

## Acceptance criteria

- [ ] Each substructure block has a decoder and a round-trip test using a fixture that exercises it within its owning record.
- [ ] A maximal `Individual` (names, events, attributes, ordinances, associations, citations, media links, notes, identifiers, restriction, change date) round-trips byte-identically.
- [ ] Place coordinates and address sub-lines round-trip through the slice-02 value parser.
- [ ] Citation and media-link pointers resolve via the slice-03 resolver.
- [ ] `mise run check` is green.

## Blocked by

- 01, 02, 03, 04.
