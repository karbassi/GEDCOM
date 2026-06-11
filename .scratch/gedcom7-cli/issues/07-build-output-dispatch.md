# build: output dispatch (.ged / .gdz / stdout)

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

The `build` command's output handling: infer the writer from the output extension (`.ged` → `dump`, `.gdz` → `dump_gedzip`), write `.ged` text to stdout when `-o` is omitted or `-o -`, and thread `--lenient` through to the writer's `strict` flag. Friendly errors for unknown output extensions.

## Acceptance criteria

- [ ] `build in.yaml -o out.ged` writes UTF-8 with BOM; `-o out.gdz` writes a GEDZIP.
- [ ] No `-o` (or `-o -`) prints GEDCOM text to stdout.
- [ ] `--lenient` emits best-effort output with warnings instead of raising.
- [ ] Unknown output extension raises a usage error (exit 2).

## Blocked by

- 04 (loader tracer)
