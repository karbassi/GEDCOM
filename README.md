# gedcom7

A [GEDCOM 7.0.18](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html) writer for Python — serialize a genealogical data model to FamilySearch GEDCOM 7 text.

> Status: early scaffolding. The data model and writer are built out incrementally; see `.scratch/` for the plan and issues.

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
