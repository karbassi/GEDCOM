# 02 — Data-type conformance lock

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-payload-conformance/PRD.md`

## What to build

A registry-sourced fixture of canonical worked examples for the 16 GEDCOM data types — derived from `GEDCOM-registries/data-type/standard` (the ABNF + worked-example tables) — vendored under `registry/` as one row per example (data type, description, expected GEDCOM payload). A table-driven test asserts the corresponding value type (`Age`, `Time`, `Latitude`/`Longitude`, the date family, `Integer`, lists, …) reproduces each expected payload, locking our hand-written formatting to the registry.

## Acceptance criteria

- [ ] A `data-type-examples.tsv` fixture is vendored under `registry/`, sourced from the registry data-type specs, with provenance recorded in `registry/README.md`.
- [ ] A table-driven test asserts each value type's output equals the expected payload for every example.
- [ ] The fixture covers the value types the library exposes (Age, Time, Latitude, Longitude, Date/DateExact/DatePeriod/range/approx, Integer, List:Text/List:Enum).
- [ ] A drift note documents how to re-source the fixture from a newer registry commit.

## Blocked by

- None - can start immediately.
