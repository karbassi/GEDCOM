# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A **reader** (`gedcom.read_text` / `gedcom.read_path`) that parses GEDCOM 7 text and GEDZIP (`.gdz`) back into the model — the structural inverse of the writer. Strict and scoped to round-tripping this library's own output (ADR-0005): cross-references resolve to object references, all 16 data types and 4 calendars parse, extension structures and enum values round-trip, and the GEDZIP unzip is guarded against path-traversal and zip-bomb members. Verified by a `write → read → write` byte-identical property test across a broad corpus. Unsupported or undeclared input raises `gedcom.ParseError`.

- GEDCOM 7.0.18 writer serializing the full standard record set (`HEAD`, `INDI`, `FAM`, `OBJE`, `REPO`, `SNOTE`, `SOUR`, `SUBM`, `TRLR`) with all 16 data types, 4 calendars, and every enumeration set.
- Reusable substructure blocks: names, events, attributes, non-events, LDS ordinances, places, addresses, identifiers, associations, restrictions, source/repository citations, multimedia links, notes, and change/creation dates.
- Extension enum values and extension structures (registered and arbitrary) with auto-emitted `HEAD.SCHMA`, plus registered `EXID` type URIs (`ExidType`).
- Spec-backed cardinality validation and two-tier strict/lenient validation.
- GEDZIP (`.gdz`) packaging.
- `gedcom` command-line tool that builds `.ged`/`.gdz` files from a YAML/JSON authoring document, with agent-friendly `guide`, `schema`, and `--json` surfaces.

[Unreleased]: https://github.com/karbassi/GEDCOM/commits/main
