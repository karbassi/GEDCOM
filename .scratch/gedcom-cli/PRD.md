# PRD: gedcom — command-line GED authoring tool

Status: done

## Problem Statement

`gedcom` is a library: it serializes an in-memory `Document` model to GEDCOM 7 text. To use it today you must write Python — construct `Individual`, `Family`, `Source` objects by hand and call `dumps`/`dump`. A genealogist, a data-pipeline author, or anyone who just wants to turn a structured description of a family tree into a conformant `.ged` file has no way to do so without programming against the model.

There is no command you can run that takes a human-authored description of people, families, and sources and produces a GEDCOM 7 file.

## Solution

A `gedcom` command-line tool that reads a friendly, declarative **authoring document** (YAML, JSON, or TOML) describing a genealogy and writes a conformant GEDCOM 7 file (`.ged`) or GEDZIP package (`.gdz`). The authoring dialect maps onto the existing model; the CLI is a thin shell over a deep, independently-testable **loader** that translates a parsed mapping into a `Document`, which the existing writer then serializes.

Reading/parsing `.ged` files remains permanently out of scope: the CLI's input is a different, friendlier format, not GEDCOM. Three subcommands:

- `gedcom build <input> -o <out>` — read an authoring document, build the `Document`, serialize to `.ged` or `.gdz` (chosen by the output extension). Strict by default; `--lenient` downgrades document-level rule violations to warnings and still emits.
- `gedcom validate <input>` — read and build the `Document`, run the two-tier validator, and report issues without writing any output. Nonzero exit on errors.
- `gedcom init` — print a commented starter authoring document (YAML by default; `--format json|toml`) so a new user has a working template to edit.

## User Stories

1. As a genealogist, I want to write my family tree in a simple YAML file and run one command to get a valid `.ged`, so that I don't have to write Python.
2. As a YAML author, I want to describe an individual with a name, sex, and birth/death events, so that the tool emits a conformant `INDI` record.
3. As an author, I want to link a husband, wife, and children into a family by referencing their handles, so that the tool emits a `FAM` with correct `HUSB`/`WIFE`/`CHIL` and derived `FAMS`/`FAMC` back-pointers.
4. As an author, I want to write dates in familiar GEDCOM form (`1 JAN 1900`, `ABT 1850`, `BET 1900 AND 1910`, `FROM 1920 TO 1930`), so that I don't have to learn a new date syntax.
5. As an author, I want native YAML/TOML dates (`1900-01-01`) to be accepted too, so that I can use my format's built-in date type.
6. As an author, I want to add sources, repositories, multimedia, and shared notes as top-level records and reference them by handle from individuals and families, so that citations and media resolve.
7. As an author, I want enumerated values (sex, name type, pedigree, restriction, role, medium, quality, ordinance status) written as plain words, so that I don't memorize tag codes.
8. As a JSON user, I want to provide the same document as JSON, so that I can generate it from another program.
9. As a TOML user, I want to provide the same document as TOML, so that I can hand-author it comfortably.
10. As a user without PyYAML installed, I want JSON and TOML to keep working with zero extra dependencies, and a clear message if I hand a YAML file without the optional extra, so that the core stays dependency-free.
11. As an author, I want to package the result as a `.gdz` GEDZIP by naming the output `out.gdz`, so that local media files are bundled.
12. As an author, I want a build error to tell me which record and field was wrong (e.g. "individuals[2].events[0].date: unrecognized date 'Jannuary 1900'"), so that I can fix my input quickly.
13. As an author, I want `gedcom validate` to list document-level issues without writing a file, so that I can check my input in CI.
14. As an author, I want `gedcom validate` to exit nonzero when there are errors, so that a CI pipeline fails on a bad tree.
15. As a new user, I want `gedcom init` to print a working, commented starter document, so that I can learn the dialect by example.
16. As a shell user, I want `gedcom build input.yaml` with no `-o` to print the GEDCOM text to stdout, so that I can pipe it.
17. As a user, I want `gedcom --version` and `--help` (and per-subcommand `--help`), so that I can discover what the tool does.
18. As an author, I want references to be order-independent (a family may reference a child defined later in the file), so that I can organize my document however I like.
19. As an author, I want a clear error when a handle reference points at a missing or wrong-typed record, so that dangling links are caught at build time.
20. As an author, I want the header (source product, submitter, language, copyright) to be authorable, with sensible defaults when omitted, so that every file has a valid `HEAD`.

## Implementation Decisions

- **New subpackage `gedcom.cli`**, kept out of the library's core import path so the library stays usable without it. Console entry point `gedcom = "gedcom.cli:main"` plus `python -m gedcom`.
- **Deep module: the loader.** `build_document(mapping) -> Document` is the heart of the feature — a pure function from a parsed mapping to a `Document`, independently testable without any file I/O or argument parsing. It owns the authoring dialect: top-level keys `header`, `submitters`, `individuals`, `families`, `sources`, `repositories`, `multimedia`, `shared_notes`.
- **Deep module: the date dialect.** A `parse_date` / `parse_date_exact` pair translates the friendly date strings (and native `date`/`datetime` values from YAML/TOML) into the existing `CalendarDate`/`ApproxDate`/`DateRange`/`DatePeriod`/`DateExact` value types. Supports the GEDCOM date heads (`ABT`/`CAL`/`EST`, `BET…AND`, `AFT`, `BEF`, `FROM…TO`), the four calendars by leading keyword, BCE, and partial dates.
- **Reference resolution.** Authoring documents link records by **handle** (the record's `xref`). The loader does two passes: construct every record and register it by handle, then wire object references (ADR-0001 object linking; the writer still derives `FAMS`/`FAMC`). A reference is any string naming a handle, with an optional surrounding `@…@` tolerated. Dangling or wrong-typed references raise a located `LoadError`.
- **Format reader.** A small dispatcher selects a parser by file extension: `.json` (stdlib `json`), `.toml` (stdlib `tomllib`), `.yaml`/`.yml` (PyYAML, imported lazily). PyYAML is an **optional extra** (`gedcom[yaml]`); the core install adds no runtime dependency. A YAML file without the extra produces a clear, actionable error.
- **Enum mapping.** Authoring values for enumerated fields accept case-insensitive member names (`female`, `birth`, `book`) and exact spec strings; `_`-prefixed extension values pass through. Unknown values raise a located `LoadError` naming the allowed set.
- **Located errors.** `LoadError` carries a dotted path to the offending node (`families[1].children[0]`). The CLI catches it, prints to stderr, and returns exit code 2 for usage/input errors, 1 for validation failures, 0 on success.
- **Output dispatch.** `build` infers the writer from the output extension: `.ged` → `dump`, `.gdz` → `dump_gedzip`. No `-o`, or `-o -`, writes `.ged` text to stdout. `--lenient` threads through to the writer's `strict` flag.
- **Scaffold.** `init` emits a static, commented template per format from a single canonical example, exercising the common fields so it doubles as documentation.

## Testing Decisions

- **Good tests assert external behavior**: the emitted GEDCOM bytes/text for a given authoring document, the validator messages, exit codes, and error messages — never private loader internals.
- **Loader** (deep module): table-driven tests mapping small authoring dicts to expected GEDCOM substrings; reference resolution (forward + backward refs, dangling ref error); enum mapping (accepted spellings + rejected value); the maximal document round-trips through `build_document` + `dumps` with no validator issues.
- **Date dialect** (deep module): table-driven over every supported head and calendar, native `date` acceptance, and malformed-string errors — mirrors `tests/test_types.py`'s example-driven style.
- **Format reader**: JSON and TOML parse with the stdlib; YAML test uses `pytest.importorskip("yaml")`; the missing-PyYAML path asserts the actionable error.
- **CLI**: invoke `main(argv)` in-process and assert exit code + stdout/stderr and the written file's bytes (via `tmp_path`); `build` to `.ged` and `.gdz`; `validate` pass/fail exit codes; `init` output re-parses and builds.
- **Prior art**: `tests/test_writer.py` (bytes + BOM), `tests/test_gedzip.py` (zip members), `tests/test_validation.py` (issues), `tests/test_coverage.py` (maximal document), `tests/test_types.py` (example-driven value types).

## Out of Scope

- Reading/parsing `.ged` files (permanently out of scope) — the input is the authoring dialect, not GEDCOM.
- A round-trip guarantee or any GEDCOM-to-authoring-document converter.
- Interactive/TUI editing, prompts, or a REPL — the tool is batch: file in, file out.
- A formal schema language (JSON Schema, etc.) for the authoring dialect — validation is by the loader's located errors plus the existing document validator.
- New genealogical concepts — the loader only exposes what the model already supports.

## Further Notes

- The authoring dialect is intentionally a thin, ergonomic projection of the model: every field corresponds to a model field, so the dialect grows for free as the model does.
- argparse (stdlib) is the parser; no CLI framework dependency. The only optional dependency in the whole project remains PyYAML, and only for YAML input.
- Build order is a sequence of end-to-end tracer bullets: each slice carries a small authoring document all the way to emitted GEDCOM with tests, rather than building a layer at a time.
