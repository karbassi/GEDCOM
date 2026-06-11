# PRD: gedcom7 — a GEDCOM 7.0.18 writer for Python

Status: done

## Problem Statement

Developers building genealogy tools in Python need to export their data as FamilySearch GEDCOM 7.0.18 — the interchange format every major genealogy application reads. Today they either hand-assemble GEDCOM text (and get the level numbering, `CONT` line-splitting, leading-`@` escaping, cross-reference bookkeeping, or UTF-8/BOM details subtly wrong, producing files other tools reject) or reach for libraries that target the older 5.5.1 format. There is no clean, typed, dependency-free Python library that takes an in-memory genealogical model and reliably emits a *conformant* GEDCOM 7 byte stream.

## Solution

A focused **writer** library, `gedcom7`, that lets a developer build a genealogical **Document** from typed domain objects — **Individual**, **Family**, **Source**, **Repository**, **Multimedia**, **Shared Note**, **Submitter**, and a **Header** — link them by ordinary Python object references, and serialize the whole thing to a standards-conformant `.ged` byte stream with one call. The library owns every fiddly detail of the GEDCOM 7 container format (cross-reference id allocation, bidirectional `FAMS`/`FAMC` integrity, `CONT` splitting, escaping, calendars, encoding, BOM) so the consumer never has to. It validates the document against the spec before writing — strictly by default, leniently on request. Reading/parsing GEDCOM is explicitly *not* part of this library.

## User Stories

1. As a genealogy-app developer, I want to construct a `Document` and serialize it to a GEDCOM 7 string with `dumps(document)`, so that I can inspect or test output without touching the filesystem.
2. As a genealogy-app developer, I want to write a `Document` to a file or binary stream with `dump(document, path_or_stream)`, so that I get a correct UTF-8 byte stream with a BOM and consistent line endings without managing encoding myself.
3. As a developer, I want the writer to emit the mandatory `HEAD` … records … `TRLR` envelope with a valid `GEDC.VERS`, so that the file is recognized as GEDCOM 7.0 by other tools.
4. As a developer, I want to create an **Individual** with names, sex, events, and attributes, so that I can represent a person.
5. As a developer, I want to attach multiple **Personal Name** structures (with name pieces and translations) to an Individual, so that I can capture alternate and translated names.
6. As a developer, I want to create a **Family** linking spouses (`HUSB`/`WIFE`) and children (`CHIL`), so that I can represent family relationships.
7. As a developer, I want children in a Family to be emitted in birth-chronological order, so that the output honors the one ordering rule the spec mandates.
8. As a developer, I want the writer to automatically emit the matching `FAMS`/`FAMC` (and `CHIL`/`FAMC`) back-pointers when I link an Individual into a Family, so that bidirectional integrity holds without my maintaining both sides.
9. As a developer, I want to reference records by Python object reference rather than by string id, so that I never hand-manage `@xref@` identifiers or risk dangling pointers.
10. As a developer, I want the writer to allocate unique, deterministic cross-reference ids at serialize time, so that output is stable and diffable across runs for a given record ordering.
11. As a developer, I want to optionally pin a preferred cross-reference id on a record, so that I can keep a meaningful or stable id when I need to.
12. As a developer, I want to use a deliberate null pointer (`@VOID@`) — e.g. a placeholder child of unknown identity in birth order — so that I can represent gaps the spec supports.
13. As a developer, I want to record individual **events** (`BIRT`, `DEAT`, `BAPM`, `BURI`, …) with dates, places, and details, so that I can capture life events.
14. As a developer, I want an event with no date/place/`Y` payload to be treated as inconclusive (not asserting occurrence), and a `Y` payload or a date/place to assert occurrence, so that occurrence semantics match the spec.
15. As a developer, I want to record family **events** (`MARR`, `DIV`, `ENGA`, …) with details, so that I can capture relationship events.
16. As a developer, I want to record **attributes** (`OCCU`, `RESI`, `NCHI`, `EDUC`, …) whose mere presence asserts they applied, so that attribute semantics match the spec.
17. As a developer, I want generic `EVEN`/`FACT` and `IDNO` to require a `TYPE`, so that the writer enforces the spec's mandatory disambiguation.
18. As a developer, I want to record **LDS ordinances** (`BAPL`, `ENDL`, `SLGC`, `SLGS`, …) with their detail and status, so that I can represent temple ordinance data, including `SLGC` requiring a `FAMC`.
19. As a developer, I want to express **non-events** (`NO MARR`, optionally with a date period), so that I can assert an event did not occur.
20. As a developer, I want to create **Source** records with author/title/publication/data and cite them from any record via a **Source Citation** (with page, quality, role), so that I can document evidence.
21. As a developer, I want **Repository** records and repository citations (with call numbers), so that I can record where sources are held.
22. As a developer, I want **Multimedia** records referencing one or more files (each with a required media type), and **Multimedia Links** (with optional crop/title) from records, so that I can attach media.
23. As a developer, I want both **Inline Notes** (`NOTE`) and reusable **Shared Note** records (`SNOTE`) with pointers, MIME, language, and translations, so that I can annotate data either way.
24. As a developer, I want **Place** structures with hierarchical names, form, translations, and map coordinates (`LATI`/`LONG`), so that I can record locations precisely.
25. As a developer, I want **Address** structures and contact details (`PHON`, `EMAIL`, `FAX`, `WWW`), so that I can record contact information.
26. As a developer, I want **identifier** structures (`REFN`, `UID`, `EXID`), so that I can attach external and user identifiers to records.
27. As a developer, I want multi-line text payloads to be split into `CONT` continuation lines automatically, so that newlines in notes and addresses serialize correctly.
28. As a developer, I want a payload whose first character is `@` to be escaped by doubling it, so that emails/handles in notes don't corrupt the file.
29. As a developer, I want all 16 data types serialized correctly — Text, Integer, Enum, Date (value/exact/period), Time, Age, List, Personal Name, Language, Media Type, Special, File Path, URI, Tag Definition, Latitude, Longitude — so that every payload is spec-conformant.
30. As a developer, I want **dates** across the 4 calendars (`GREGORIAN`, `JULIAN`, `FRENCH_R`, `HEBREW`) with approximations, ranges, and periods, with the calendar omitted when Gregorian and emitted per-date in ranges, so that historical dates are represented correctly.
31. As a developer, I want dual-date and year-slash inputs handled via a `PHRASE` substructure rather than the forbidden slash notation, so that the output stays conformant.
32. As a developer, I want **enumerated** payloads exposed as typed enums (`Sex`, `Role`, `Medi`, `Pedi`, `Quay`, `Resn`, `NameType`, …) with autocomplete and type-checking, so that I can't mistype a value.
33. As a developer, I want to supply a `_`-prefixed extension value where the spec permits extension enums, so that I'm not boxed in by the standard set.
34. As a developer, I want any extension tags I actually use to be auto-declared in a generated `HEAD.SCHMA` block, so that files using extensions remain conformant.
35. As a developer, I want value objects (`Date`, `Age`, `Latitude`, …) to reject invalid values at construction, so that I find mistakes immediately rather than in the output.
36. As a developer, I want a serialize-time validation pass that checks required substructures, xref uniqueness, bidirectional integrity, and forbidden `OBJE`↔`SOUR`/`SNOTE`↔`SOUR` cycles, so that I can't accidentally produce an invalid file.
37. As a developer, I want validation to be strict by default (raise) but switchable to lenient (warn and emit best-effort), so that I can choose between safety and tolerance of incomplete data.
38. As a developer, I want deprecation warnings for spec-deprecated constructs (`ADR1/2/3`, `EXID` without `TYPE`, deprecated `ord-STAT` values, `HEAD.SOUR.DATA`), so that I'm nudged toward forward-compatible output.
39. As a developer, I want the writer to reject banned control characters in payloads, so that I never emit a file that violates the character rules.
40. As a developer, I want to choose the line terminator (default LF) and have it applied uniformly, so that output matches my platform conventions.
41. As a developer, I want the library to have zero runtime dependencies and ship typed (`py.typed`), so that it's lightweight and type-checks cleanly in my project.
42. As a maintainer, I want golden-file tests that build a `Document` and assert exact `.ged` bytes, so that serialization regressions are caught.
43. As a maintainer, I want each data type and the line primitive unit-tested against the spec's own ABNF examples, so that conformance is demonstrable.
44. As a future user, I want a path to GEDZIP (`.gdz`) output, so that I can bundle media with the dataset later (post-v1).

## Implementation Decisions

- **Domain-word model.** Public classes use domain words (`Individual`, `Family`, `Multimedia`, `Source`, `Repository`, `SharedNote`, `Submitter`, `Header`); the GEDCOM wire tag is an internal encoding detail, never a public name. (CONTEXT.md)
- **Document aggregate.** A `Document` owns the `Header`, the record collection, and the cross-reference id namespace, and is the unit passed to the writer. (CONTEXT.md)
- **Object-reference linking + auto xref (ADR-0001).** Records link by Python object reference; the writer mints document-local `@xref@` ids deterministically at serialize time (optional per-record override) and resolves pointers by object identity. Bidirectional `FAMS`/`FAMC` and `CHIL`/`FAMC` integrity is **derived**, not hand-maintained. Unresolvable references and forbidden cycles are rejected.
- **Two-tier validation, strict by default (ADR-0002).** Value-level invariants are enforced at construction by the value types; document-level rules run in a dedicated serialize-time pass. Default mode raises; a lenient mode warns and emits best-effort.
- **Frozen values, mutable records (ADR-0003).** Value/datatype objects are frozen dataclasses; record objects are mutable so reference cycles the format requires (e.g. `BIRT.FAMC` ⇄ `CHIL`) can be wired after construction.
- **Typed enums + escape hatch.** One Python enum per enumeration set, plus acceptance of a `_`-prefixed extension string anywhere the spec permits extension enum values.
- **Output API.** `dumps(document) -> str` for convenience (no BOM); `dump(document, path_or_stream)` writes the authoritative UTF-8 byte stream with a leading BOM and the chosen EOL.
- **Module decomposition (9 deep modules).**
  - `lines` — the `Line(level, xref, tag, value)` primitive and renderer; the only place that knows the §1 byte grammar (delimiter, leading-`@` escaping, `CONT` splitting, EOL, BOM, banned-char rejection).
  - `types` — the 16 data-type serializers and the 4 calendars, as pure functions / frozen value classes.
  - `enums` — typed enums per set + extension escape hatch + permitted-value checks.
  - `model` — record dataclasses (mutable), value types (frozen), substructure blocks, and the `Document` aggregate.
  - `xref` — xref-namespace allocation, object-identity→`@xref@` resolution, derived integrity back-pointers.
  - `serialize` — model → ordered `Line` sequence (per-record/substructure encoders, substructure ordering, `CHIL` birth-order).
  - `validation` — the document-level rule pass (required substructures, integrity, uniqueness, cycles, deprecations) with strict/lenient modes.
  - `writer` — public surface wiring validation → xref → serialize → lines into `dumps`/`dump`.
  - `gedzip` — optional `.gdz` packaging (post-v1 slice).
- **Tech stack.** Python 3.12+ (CI matrix 3.12/3.13/3.14), `uv` for venv/deps/build, `mise` for runtimes and tasks, `ruff` + `mypy` (strict) + `pytest`, zero runtime dependencies, `src/` layout, `py.typed`.

## Testing Decisions

- **What makes a good test here:** assert external behavior — the exact bytes/string a `Document` serializes to, the values a data-type function returns, the errors validation raises — never internal call structure. The spec's own ABNF and worked examples are the oracle.
- **`lines`** — unit tests for delimiter handling, leading-`@` escaping (and only-first-char rule), `CONT` splitting on embedded newlines (including blank lines), EOL selection, BOM presence in byte output, and banned-character rejection.
- **`types`** — table-driven unit tests for each data type against the spec's examples: dates across all 4 calendars (approximations, ranges, periods, BCE/no-year-0, Hebrew Adar), times, ages, latitude/longitude formatting, list joining, personal-name slash handling.
- **`xref` + `validation`** — tests for deterministic id allocation, object-identity resolution, `@VOID@`, derived `FAMS`/`FAMC` back-pointers, xref uniqueness, required-substructure enforcement, forbidden-cycle detection, and the strict-vs-lenient behavior split.
- **`serialize` + `writer`** — end-to-end golden-file tests: build representative `Document`s (a minimal valid file; a rich Individual+Family graph; notes/sources/media; extension enum + auto-`SCHMA`) and assert the exact `.ged` output.
- **Prior art:** none yet (greenfield). The `tdd` skill's red-green-refactor loop and golden-file pattern are the model; the smoke test in `tests/test_smoke.py` is the seed.

## Out of Scope

- **Reading/parsing** GEDCOM of any version — this is a writer only.
- **GEDCOM 5.5.1** or any pre-7 version output.
- **Custom extension records/substructures** (arbitrary `_`-tag structures with URIs) — v1 supports only extension *enum values* plus auto-emitted `HEAD.SCHMA`; custom extension structures are deferred.
- **GEDZIP (`.gdz`)** packaging — designed for but deferred to a post-v1 slice.
- **Data validation beyond the spec** (e.g. genealogical plausibility, date-vs-age consistency) — only structural/format conformance is enforced.
- **Round-tripping or preserving exact original xref ids** from some source file — ids are treated as transient per the spec.

## Further Notes

- Authoritative references in-repo: `docs/spec/gedcom7-writer-map.md` (the implementer-facing spec map), `CONTEXT.md` (glossary), and `docs/adr/0001–0003` (the locked decisions). These should be kept in sync as implementation proceeds.
- The natural build order is bottom-up and tracer-bullet: `lines` + a couple of `types` first, then a minimal `HEAD`/`TRLR` end-to-end write, then records slice-by-slice (Individual → Family → Source/Repository → Multimedia/Notes), with validation and extensions layered in. `/to-issues` will cut these into independently-grabbable vertical slices.
- Tag/URI collisions (`CENS`, `NCHI`, `RESI` across INDI/FAM; `ADOP`, `HUSB`/`WIFE` as both tags and enum values) must be disambiguated by superstructure in the `serialize`/`enums` layers.
