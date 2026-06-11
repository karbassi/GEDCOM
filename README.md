# gedcom7

A [GEDCOM 7.0.18](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html) writer for Python — serialize a genealogical data model to FamilySearch GEDCOM 7 text.

> Status: feature-complete for the standard structures. The writer serializes the full GEDCOM 7 record set (HEAD, INDI, FAM, OBJE, REPO, SNOTE, SOUR, SUBM, TRLR) with all 16 data types, 4 calendars, every enumeration set, the reusable substructure blocks (names, events, attributes, non-events, LDS ordinances, places, addresses, identifiers, associations, restrictions, source/repository citations, multimedia links, notes, change/creation dates), extension enum values and extension *structures* (registered + arbitrary) with auto-emitted `HEAD.SCHMA`, registered `EXID` type URIs (`ExidType`), spec-backed cardinality validation, two-tier strict/lenient validation, and GEDZIP (`.gdz`) packaging. Code is drift-locked to the vendored FamilySearch registries (`registry/`). See `.scratch/` for the plan and issues.

### Known limitations

- **`INDI.FAMC` pedigree/status detail** (`PEDI`/`STAT` on a membership) and **event-level `FAMC`** (`BIRT`/`CHR`/`ADOP`) — `FAMS`/`FAMC` are derived as bare pointers (ADR-0001); per-membership detail is deferred pending an ADR decision (tracked as issue #18).
- **Reading/parsing** GEDCOM — permanently out of scope; this is a writer only.

## Tech stack

- **Python 3.12+** (tested against 3.12 / 3.13 / 3.14), zero runtime dependencies — the data model is plain `dataclasses`.
- **[mise](https://mise.jdx.dev/)** manages the runtimes and runs tasks; config lives in `.config/mise/`.
- **[uv](https://docs.astral.sh/uv/)** manages the virtualenv, dependencies, and build.
- **ruff** (lint + format), **mypy** (strict), **pytest** (tests).

## Getting started

```sh
mise install      # install Python + uv
mise run install  # uv sync — create the venv and install dev deps
mise run check    # lint + typecheck + test
```

### Tasks

| Task | What it does |
| --- | --- |
| `mise run install` | `uv sync` — venv + dev dependencies |
| `mise run test` | run pytest (args pass through) |
| `mise run lint` | `ruff check` |
| `mise run fmt` | `ruff format` + `ruff check --fix` |
| `mise run typecheck` | `mypy` (strict) |
| `mise run check` | the full gate: lint + typecheck + test |

## License

MIT
