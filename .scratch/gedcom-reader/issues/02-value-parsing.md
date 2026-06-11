# 02 — Value parsing: the 16 data types

Status: ready-for-agent
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

`src/gedcom/parse/_values.py` — the inverse of `gedcom.types` and the enum/integer/list helpers. Parse GEDCOM payload strings back into the value types the model uses: dates across all four calendars (`GREGORIAN`, `JULIAN`, `FRENCH_R`, `HEBREW`) including periods, ranges, and approximation qualifiers (`ABT`/`CAL`/`EST`/`BEF`/`AFT`/`BET…AND`/`FROM…TO`); exact dates and times; ages; latitude/longitude; enumerations; non-negative integers; and text / text-lists. Invalid payloads raise `ParseError`; values the value types reject at construction propagate that rejection as a `ParseError` at the offending payload.

This is a pure value-layer slice — no document assembly — verified directly against the canonical examples.

## Acceptance criteria

- [ ] Every canonical worked example used by the writer's data-type tests parses back to a value equal to the one that produced it (lossless round-trip per type).
- [ ] All four calendars round-trip, including period/range/approximation forms.
- [ ] An out-of-range coordinate / malformed age / unknown enum value raises `ParseError`.
- [ ] Tests reuse the registry-sourced data-type fixture where one exists (see `gedcom-payload-conformance`), asserting `parse(render(v)) == v`.
- [ ] `mise run check` is green.

## Blocked by

- 01 (needs `ParseError` and the `parse/` package).
