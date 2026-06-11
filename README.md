# gedcom7

A [GEDCOM 7.0.18](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html) writer for Python — serialize a genealogical data model to FamilySearch GEDCOM 7 text.

> Status: feature-complete for the standard structures. The writer serializes the full GEDCOM 7 record set (HEAD, INDI, FAM, OBJE, REPO, SNOTE, SOUR, SUBM, TRLR) with all 16 data types, 4 calendars, every enumeration set, the reusable substructure blocks (names, events, attributes, non-events, LDS ordinances, places, addresses, identifiers, associations, restrictions, source/repository citations, multimedia links, notes, change/creation dates), extension enum values and extension *structures* (registered + arbitrary) with auto-emitted `HEAD.SCHMA`, registered `EXID` type URIs (`ExidType`), spec-backed cardinality validation, two-tier strict/lenient validation, and GEDZIP (`.gdz`) packaging. A command-line tool (`gedcom`) builds `.ged`/`.gdz` files from a friendly YAML/JSON/TOML authoring document. Code is drift-locked to the vendored FamilySearch registries (`registry/`). See `.scratch/` for the plan and issues.

### Known limitations

- **Reading/parsing** GEDCOM — permanently out of scope; this is a writer only. The CLI's input is a separate, friendlier authoring dialect, not GEDCOM.

## Command-line tool

The `gedcom` command turns a declarative **authoring document** — a YAML, JSON, or TOML file describing people, families, and sources — into a conformant GEDCOM 7 file. No Python required.

```sh
gedcom init -f yaml > tree.yaml    # scaffold a starter document to edit
gedcom validate tree.yaml          # check it without writing output
gedcom build tree.yaml -o tree.ged    # build GEDCOM text (.ged)
gedcom build tree.yaml -o tree.gdz    # or a GEDZIP package (.gdz)
gedcom build tree.yaml             # no -o: print GEDCOM to stdout
```

`python -m gedcom7` is equivalent to the `gedcom` command. Run `gedcom help` (or `gedcom help <command>`) for usage. Exit codes: `0` success, `1` validation failure, `2` usage/input error. `build` is strict by default; `--lenient` downgrades document-level rule violations to warnings and emits anyway.

### Driving it from an AI agent

The CLI is built to be agent-friendly. An agent can learn the whole dialect and drive the workflow without guessing:

```sh
gedcom guide                       # the workflow + rules, as a short playbook
gedcom schema                      # machine-readable dialect: sections, enums,
                                   #   date forms, references, a worked example (JSON)
gedcom validate tree.yaml --json   # {"ok": false, "issues": [...]} or {"ok": true, ...}
gedcom build tree.yaml -o out.ged --json   # {"ok": true, "output": "...", "records": N}
```

With `--json`, errors are structured too — `{"ok": false, "error": {"path": "individuals[2].events[0].date", "message": "…"}}` — so an agent can locate and fix the offending field, then re-validate. The `schema` enum vocabularies are derived live from the library, so they never drift from what `build` accepts.

### Authoring dialect

The document is a mapping of top-level **record sections**, each a list of records. Records link to one another by **handle** — the record's `xref` — and references are order-independent (a family may name a child defined later in the file); a surrounding `@…@` is tolerated.

```yaml
header:
  source: { product: My Genealogy, version: "1.0" }
  language: en

individuals:
  - xref: I1
    name: John /Smith/          # surname goes between slashes
    sex: M                       # enum: name or spec value (male / M)
    events:
      - { tag: BIRT, date: 1 JAN 1900, place: "Boston, MA, USA" }
      - { tag: DEAT, date: ABT 1970 }
    sources:
      - { source: S1, page: "p. 42" }

  - { xref: I2, name: Mary /Jones/, sex: F }
  - { xref: I3, name: Sara /Smith/, sex: F }

families:
  - xref: F1
    husband: I1                  # handle references; @I1@ also accepted
    wife: I2
    children: [I3]              # birth order; FAMS/FAMC are derived for you
    events:
      - { tag: MARR, date: 5 JUN 1925 }

sources:
  - { xref: S1, title: Massachusetts Vital Records }
```

| Section | Record |
| --- | --- |
| `individuals` | a person (`INDI`) |
| `families` | a family (`FAM`) — `husband`/`wife`/`children` |
| `sources` | a source (`SOUR`) |
| `repositories` | an archive (`REPO`) |
| `multimedia` | a media record (`OBJE`) — `files` |
| `shared_notes` | a reusable note (`SNOTE`) |
| `submitters` | a contributor (`SUBM`) |

- **Dates** use familiar GEDCOM forms: `1 JAN 1900`, `JAN 1900`, `1900`, `100 BCE`, `ABT/CAL/EST 1850`, `BET 1900 AND 1910`, `AFT 1900`, `BEF 1910`, `FROM 1920 TO 1930`. Other calendars take a leading keyword: `JULIAN 1 MAR 1700`, `HEBREW 1 TSH 5700`, `FRENCH_R 1 VEND 1`. Native YAML/TOML dates (`1900-01-01`) are accepted too.
- **Enums** (`sex`, name `type`, `pedigree`, `restriction`, `role`, `medium`, `quality`, ordinance `status`, …) accept the member name (`female`, `birth`, `book`) or the exact spec string; a `_`-prefixed value passes through as an extension.
- **Errors** are located: a bad date, reference, or enum reports its path, e.g. `individuals[2].events[0].date: …`.
- The authoring dialect is a thin projection of the library model — every key maps to a model field. `gedcom init` prints a complete, commented example, and `gedcom schema` describes every section and enum.

### Installing YAML support

JSON and TOML inputs use only the standard library. YAML needs PyYAML, an optional extra:

```sh
pip install "gedcom7[yaml]"
```

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
