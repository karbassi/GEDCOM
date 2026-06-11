# PRD: gedcom — registry alignment & registered extensions

Status: done

## Problem Statement

`gedcom` v1 is feature-complete for the standard structures, but several correctness and ergonomics facts about GEDCOM 7 live in two FamilySearch sources we only partially consume: the spec repo (`familysearch/GEDCOM`, whose terminology tables we vendored as TSVs and drift-lock our enums against) and the live terminology registry (`FamilySearch/GEDCOM-registries`, the canonical home of calendars, months, enum payloads, EXID type URIs, and registered extension structures). Three gaps follow from this:

- **EXID is a footgun.** The spec deprecates `EXID` without a `TYPE`, and we only emit a lenient warning. The 14 well-known external-identifier authorities (FindAGrave, BillionGraves, WikiTree, FamilySearch IDs, AFN, RFN, RIN, GOV-ID) each have an official TYPE URI in the registry, but a consumer has no typed, discoverable way to use them — they must hand-copy a URI string and hope it is exact.
- **Calendars are hand-transcribed.** Our month lists and epoch markers (`BCE`) for the four calendars were typed in by hand. The registry stores each calendar's *ordered* month list and its permitted epochs authoritatively; nothing guards our copies against a transcription error (wrong order → wrong month number → silently wrong dates).
- **Validation is hand-rolled.** Our validation rules are bespoke per structure. The spec ships machine-readable cardinality and substructure tables (`cardinalities.tsv`, `substructures.tsv`) describing which substructures are required/optional and singular/list under each structure — an authoritative basis we don't yet use.
- **Registered extensions are unreachable.** The registry publishes 14 *registered* `_`-prefixed extension structures (Ancestry_*, MagiKey_*, `_DATE`, `_SOUR`) with authoritative tag→URI mappings. v1 supports extension enum *values* but not extension *structures*, so a consumer cannot emit even a registered, well-known one.

## Solution

Make the FamilySearch registries a first-class, drift-locked backbone of the library and surface what they offer to consumers:

- A typed **ExidType** vocabulary exposing the 14 registered EXID TYPE URIs, so an **Identifier** of kind `EXID` can be given a discoverable, correct type (`Identifier("EXID", value, type=ExidType.FIND_A_GRAVE_MEMORIAL)`), drift-locked to the registry.
- **Calendar/month/epoch** data vendored from the registry and our in-code calendar definitions drift-locked to it — month order and permitted epochs verified against the authoritative source.
- **Registry-driven cardinality validation**: validation rules derived from the spec's cardinality/substructure tables rather than hand-written, so the validator tracks the spec.
- **Registered extension structures**: a bounded mechanism to emit the registry's registered `_`-prefixed structures with their authoritative tag→URI `HEAD.SCHMA` declarations, drift-locked so our registered set matches the registry.

Reading/parsing remains out of scope. Arbitrary user-defined extension structures remain out of scope — only *registered* ones are supported here.

## User Stories

1. As a genealogy-app developer, I want an `ExidType` value for each well-known authority (FindAGrave, BillionGraves, WikiTree, FamilySearch, AFN, RFN, RIN, GOV-ID), so that I can attach a correct external identifier without copying a URI by hand.
2. As a developer, I want `Identifier` of kind `EXID` to accept an `ExidType` (or a raw URI string) as its `TYPE`, so that the emitted `EXID`/`TYPE` pair is conformant and the deprecation footgun disappears for the common case.
3. As a developer, I want the writer to emit the exact registry URI for each `ExidType` (e.g. `https://www.findagrave.com/memorial/`, `https://gedcom.io/terms/v7/AFN`), so that downstream tools recognize the identifier authority.
4. As a maintainer, I want a drift test that fails if our `ExidType` set diverges from `GEDCOM-registries/uri/exid-types`, so that the library stays aligned as the registry evolves.
5. As a maintainer, I want each calendar's month list and permitted epochs drift-locked to `GEDCOM-registries/calendar/standard`, so that a transcription error in month order or an epoch marker is caught automatically.
6. As a developer, I want non-Gregorian dates to serialize with the correct month tokens in the correct positions for all four calendars, so that the month number maps to the right month.
7. As a developer, I want `BCE` emitted only for calendars that permit an epoch (Gregorian, Julian) and never for those that don't (French Republican), so that I cannot produce an invalid date.
8. As a maintainer, I want validation cardinality rules derived from the spec's `cardinalities.tsv`/`substructures.tsv`, so that "this substructure is required / must be singular / may repeat" tracks the spec rather than my memory.
9. As a developer, I want the validator to flag a missing required substructure (e.g. an `OBJE` with no `FILE`) and an illegally repeated singular substructure, citing the structure, so that I learn what is wrong before the file ships.
10. As a developer, I want strict mode to raise on cardinality violations and lenient mode to collect them as issues, consistent with the existing two-tier validation (ADR-0002).
11. As a developer, I want to attach a *registered* extension structure (e.g. an Ancestry or MagiKey extension) to a record, so that I can emit data those ecosystems expect.
12. As a developer, I want a registered extension structure to auto-emit its `HEAD.SCHMA` `TAG`→URI declaration using the registry's authoritative URI, so that the file is self-describing and conformant.
13. As a maintainer, I want a drift test asserting our supported registered-extension set and their URIs match `GEDCOM-registries/structure/extension`, so that the mappings cannot silently rot.
14. As a maintainer, I want the vendored registry data (exid-types, calendars, months, registered extensions) recorded with its upstream commit provenance, so that the lock has a known source of truth.

## Implementation Decisions

- **Vendored registry expansion.** Extend `registry/` beyond the five TSVs with the registry data this PRD locks against — EXID types, calendars, months, and registered extension structures — each recorded with upstream commit provenance in `registry/README.md`. Tests read the vendored copy (offline, deterministic), not the network.
- **ExidType vocabulary.** A typed enumeration of the 14 registered EXID TYPE URIs whose value is the exact registry `uri`. The `Identifier` model's EXID `type` accepts an `ExidType` or a raw `str` (escape hatch for unregistered authorities). Serialization emits the URI as the `TYPE` payload. This is additive — existing string usage keeps working.
- **Calendar drift-lock.** Keep the in-code calendar definitions as the runtime source, but add a drift test that verifies each calendar's ordered month list and permitted epoch set against the vendored calendar YAML. Fix any epoch handling so `BCE` is only emitted where the calendar permits an epoch.
- **Cardinality validation engine.** A deep module that ingests the spec's cardinality/substructure tables into an in-memory rule set (minimum/maximum occurrences per substructure under each superstructure) and checks a serialized document's structure tree against it, yielding `Issue`s. Wired into the existing `validate()` strict/lenient flow rather than replacing the bespoke semantic rules wholesale — cardinality is the spec-backed layer; existing value-level rules remain.
- **Registered extension structures.** A bounded model representation for a registered `_`-prefixed structure (its tag, payload, and registry URI) attachable where the registry permits it, serialized as the corresponding `_`-tag lines and contributing its tag→URI to the auto-emitted `HEAD.SCHMA` (reusing the existing schema-collection path from issue #15 of the v1 PRD). Only structures present in the vendored registered-extension set are accepted.

## Testing Decisions

- **Good tests assert external behavior**: emitted bytes (golden), validator issues (presence/absence + message), and registry alignment (drift). They do not assert private structure.
- **Drift tests** are the headline pattern here, extending `tests/test_registry.py`: `ExidType` ↔ `uri/exid-types`; calendar months+epochs ↔ `calendar/standard`; registered extensions ↔ `structure/extension`. Each fails loudly if the vendored registry and our code diverge.
- **Golden/byte tests** for: an `Identifier` EXID with an `ExidType` emitting the right `TYPE` URI; a non-Gregorian date emitting correct month tokens; a registered extension structure emitting its `_`-tag lines plus the matching `HEAD.SCHMA`.
- **Validation tests** for: a missing required substructure flagged; an over-repeated singular substructure flagged; strict raises / lenient collects.
- **Prior art**: `tests/test_registry.py` (drift), the per-structure golden tests across `tests/test_*.py`, and `tests/test_validation.py` (issue assertions, strict/lenient).

## Out of Scope

- Reading/parsing GEDCOM (permanently out of scope for this library).
- Arbitrary, *unregistered* user-defined extension structures — only registry-listed ones are supported.
- GEDZIP (`.gdz`) packaging.
- `INDI.FAMC` pedigree/status detail and event-level `FAMC` (still derived as bare pointers per ADR-0001).
- Full code-generation of the model from the registry — we drift-lock curated code, we do not generate it (the TSVs store URIs, not payload strings, and member names need curation).

## Further Notes

- Provenance for the new vendored data should pin a specific `GEDCOM-registries` commit, matching how `registry/README.md` pins the `familysearch/GEDCOM` commit for the TSVs.
- Sample registry shapes observed: EXID type YAML carries `label`, `uri`, `specification`, `documentation`; calendar YAML carries `standard tag`, an *ordered* `months:` URI list, and an `epochs:` list (empty for French Republican). These are the fields the locks read.
- The EXID `TYPE` payload is the registry `uri` verbatim — for some authorities a `gedcom.io/terms` URI (AFN/RFN/RIN), for others the authority's own base URL (FindAGrave, GOV).
