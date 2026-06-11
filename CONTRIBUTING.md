# Contributing to GEDCOM

Thanks for your interest in improving GEDCOM. This document covers how to set up a development environment, run the checks, and submit changes.

## Scope and direction

GEDCOM is a **writer only** — it serializes a genealogical data model to FamilySearch GEDCOM 7 text. Reading or parsing GEDCOM is permanently out of scope. The CLI's input is a separate, friendlier authoring dialect (YAML/JSON/TOML), not GEDCOM. Please keep proposals within this scope; see `CONTEXT.md` and `docs/adr/` for the domain language and the decisions behind it.

## Development setup

The project uses [mise](https://mise.jdx.dev/) to manage runtimes and tasks, and [uv](https://docs.astral.sh/uv/) for the virtual environment, dependencies, and builds.

```sh
mise install      # install pinned Python (3.12–3.14) and uv
mise run install  # sync the venv and dev dependencies via uv
```

If you prefer not to use mise, any Python 3.12+ with `uv sync` works; the mise tasks are thin wrappers around `uv run`.

## Checks

The full gate is lint + typecheck + tests. Run it before opening a PR:

```sh
mise run check       # lint, typecheck, and tests under 100% coverage (the full gate)

mise run lint        # ruff check (no fixes)
mise run typecheck   # mypy (strict)
mise run test        # pytest — extra args pass through, e.g. mise run test -k cli
mise run cov         # pytest under coverage; fails under 100%
mise run fmt         # ruff format + lint autofixes
```

Equivalent without mise: `uv run python -m ruff check .`, `uv run python -m mypy`, `uv run python -m pytest`.

The suite holds **100% line coverage** of `src/gedcom`, enforced by `mise run cov` (and therefore `mise run check`). New code needs tests that keep it there; genuinely unreachable defensive branches may be marked `# pragma: no cover` with a one-line reason.

## Conventions

- **Code is drift-locked to the vendored FamilySearch registries** under `registry/`. Behavior that depends on the spec (enumerations, cardinality, calendars, EXID types) should derive from those registries rather than hard-coding values, so it never drifts from what the standard defines.
- New behavior needs tests. The suite is the contract; keep it green and add coverage for the cases you change.
- Match the surrounding style — the codebase is fully type-annotated and passes `mypy --strict`.
- Keep the CLI's `schema`/`guide` output in sync with what `build` actually accepts; the schema vocabularies are derived live from the library to prevent drift.

## Submitting changes

1. Branch off `main`.
2. Make your change with tests and keep `mise run check` green.
3. Add a note under the `Unreleased` section of `CHANGELOG.md` if the change is user-facing.
4. Open a pull request describing the motivation and the change. Link any related issue.

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
