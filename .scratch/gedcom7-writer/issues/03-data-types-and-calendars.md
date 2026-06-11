# 03 — Data types + calendars

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

The `types` module: pure serializers / frozen value classes for all 16 GEDCOM data types (Text, Integer, Enum token, DateValue/DateExact/DatePeriod, Time, Age, List:Text/List:Enum, PersonalName, Language, MediaType, Special, FilePath, URI, TagDef, Latitude, Longitude) and the 4 known calendars (GREGORIAN omitted by default, JULIAN, FRENCH_R, HEBREW). Cover approximations (`ABT`/`CAL`/`EST`), ranges (`BET`/`AND`, `AFT`, `BEF`), periods (`FROM`/`TO`), `BCE` with no year 0, per-date calendar within ranges, and dual-date handled via a `PHRASE`. Value types reject invalid input at construction and are frozen (ADR-0002/0003).

## Acceptance criteria

- [ ] Each data type serializes to match the spec's ABNF worked examples (table-driven tests).
- [ ] Dates: Gregorian calendar omitted, non-Gregorian emitted; calendar applied per-date in `FROM x TO y`; `BCE` with no year 0; Hebrew `ADR`→`ADS` in common years when the year is known.
- [ ] `Latitude`/`Longitude` reject out-of-range values; `Age` rejects malformed input; constructed value objects are frozen.
- [ ] Year-slash dual dates are never emitted; the original notation is carried in a `PHRASE`.
- [ ] Demonstrated end-to-end via a Header `DATE` (DateExact) + `TIME`.
- [ ] Unit tests cover every data type and all four calendars against spec examples.

## Blocked by

- #01 Walking skeleton: minimal valid document
