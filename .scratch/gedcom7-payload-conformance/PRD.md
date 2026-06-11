# PRD: gedcom7 — payload & structure conformance

Status: done

## Problem Statement

PRD2 locked the library's *shape* to the FamilySearch registries — which substructures may appear under each structure and how many times (cardinality), plus enum/calendar/EXID/extension vocabularies. Two registry assets remain under-used, and they govern the *contents* of each line rather than its shape:

- **`payloads.tsv`** maps every structure to its payload data type — `Y|<NULL>`, plain string, enum, **non-negative integer**, pointer, date, list, or *empty* (no payload). The library enforces most of these at construction (typed enums, frozen value types, object-reference pointers), but not all: free-string fields such as `Attribute.value` accept anything, so `Attribute("NCHI", "five")` serializes to a `NCHI` line whose payload should be a non-negative integer, and nothing flags it. There is no spec-backed backstop verifying an emitted line's value matches its declared type.
- **`data-type/`** provides the canonical ABNF and worked examples for the 16 data types. Our value types (`Age`, `Time`, `Latitude`/`Longitude`, the date family, …) are hand-written and tested against the spec, but those expectations are not *locked* to a registry-sourced fixture, so a future edit could silently diverge from the canonical examples.

There is also no executable check that the writer actually *covers* the standard structure set it claims to.

## Solution

Complete the registry-locking story by constraining line *payloads* and value *formatting*, and by proving coverage:

- **Payload-type validation**: using `payloads.tsv` and the per-line structure resolver PRD2 already built, validate each emitted line's value against its declared data type — non-negative-integer payloads parse as such, empty-payload (container) structures carry no value, and everything else gets a spec-backed backstop. Wired into the existing two-tier `validate()` (ADR-0002).
- **Data-type conformance lock**: a registry-sourced fixture of canonical worked examples for the 16 types, with a test asserting the value types reproduce them — drift protection on formatting.
- **Structure coverage audit**: a maximal-coverage `Document` fixture exercised through the writer, whose emitted standard tags are checked against the standard structure-tag set from `substructures.tsv`, with a documented exclusion list — a concrete, regression-protective coverage measure.

Reading/parsing remains permanently out of scope. This PRD adds no new genealogical concepts; it hardens conformance of what the writer already emits.

## User Stories

1. As a developer, I want a `NCHI`/`AGE`-style structure whose payload should be a non-negative integer to be flagged when I pass a non-integer string, so that I don't ship a malformed line.
2. As a developer, I want a container (empty-payload) structure to be flagged if it somehow carries a value, so that structural-only tags stay value-less.
3. As a developer, I want payload-type checks to run in the same strict/lenient `validate()` flow as cardinality (ADR-0002), so that conformance is one consistent pass.
4. As a developer, I want a valid document to produce zero payload-type issues, so that the check is trustworthy (no false positives).
5. As a maintainer, I want payload-type rules sourced from `payloads.tsv` rather than hand-written, so that they track the spec.
6. As a maintainer, I want the 16 data types' output locked to a registry-sourced set of canonical worked examples, so that a formatting regression fails a test.
7. As a maintainer, I want a drift test that fails if our payload/data-type fixtures diverge from the vendored registry, so that the lock has a known source of truth.
8. As a maintainer, I want an executable coverage audit that lists which standard structure tags the writer can and cannot emit, so that the "full standard coverage" claim is verified, not asserted.
9. As a maintainer, I want any intentionally-unsupported structure recorded in an explicit exclusion list (not silently omitted), so that coverage gaps are visible.

## Implementation Decisions

- **Payload rule source.** Vendor `payloads.tsv` into the package data (`src/gedcom7/_spec/`, as PRD2 did for the cardinality tables) and load it into a payload-type map keyed by structure URI. A drift test keeps the packaged copy byte-identical to `registry/`.
- **Payload validation engine.** Extend the structure-tree walk (the same resolver that powers cardinality) to classify each line's declared payload type and check the line's value: non-negative-integer types parse as `>= 0`; empty-payload types must have no value; pointer/enum/`Y|<NULL>` types are already guaranteed by the model and serve as a backstop only. Emit `Issue`s into the existing `validate()` pipeline; do not duplicate value-level errors the construction layer already raises.
- **Data-type fixture.** A curated, registry-sourced fixture (one row per canonical worked example: data type, description, expected GEDCOM payload) vendored under `registry/`, with a test asserting the corresponding value type reproduces each expected payload.
- **Coverage audit.** A maximal-coverage `Document` built in the test suite, serialized once; the set of emitted tags (resolved to standard structure URIs) is compared against the standard, non-extension structure tags derived from `substructures.tsv`. Unsupported structures live in an explicit, documented exclusion set; the audit fails if an un-excluded standard structure has no serialization path.

## Testing Decisions

- **Good tests assert external behavior**: validator issues (present/absent + message), emitted bytes, and registry alignment (drift). No assertions on private structure.
- **Payload validation**: a malformed non-negative-integer payload is flagged; an over-filled container structure is flagged; strict raises / lenient collects; every existing golden document yields zero payload issues (no false positives — the critical guard).
- **Data-type lock**: table-driven test over the vendored canonical examples; drift test vs the registry fixture.
- **Coverage audit**: asserts the emitted standard-tag set covers the registry's standard structure tags minus the documented exclusions.
- **Prior art**: `tests/test_registry.py` (drift), `tests/test_cardinality.py` + `tests/test_validation.py` (structure walk, strict/lenient), `tests/test_types.py` (value-type examples).

## Out of Scope

- Reading/parsing GEDCOM (permanently out of scope).
- Re-validating constraints the construction layer already enforces (enum membership, value-type formats, pointer validity) — payload validation is a backstop, not a re-implementation.
- Deprecation handling — the registries carry no deprecation metadata to act on.
- Full ABNF-grammar execution — the data-type lock uses curated worked examples, not a general ABNF engine.

## Further Notes

- This is deliberately a smaller PRD than PRD1/PRD2: PRD2 already extracted the high-value registry content (EXID, calendars, cardinality, extensions). These three items are the remaining worthwhile, machine-usable extractions from `familysearch/GEDCOM` and `FamilySearch/GEDCOM-registries`; after this, the repos are effectively tapped.
- Provenance for any newly vendored data pins the same `GEDCOM-registries`/`familysearch/GEDCOM` commits already recorded in `registry/README.md`.
