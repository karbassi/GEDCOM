# Authoring-document format reader

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

A format dispatcher that turns an input path into a parsed mapping: `.json` via stdlib `json`, `.toml` via stdlib `tomllib`, `.yaml`/`.yml` via lazily-imported PyYAML. PyYAML is an optional extra (`gedcom[yaml]`); a YAML file without it raises a clear, actionable error. Non-mapping top-level content is rejected.

## Acceptance criteria

- [ ] JSON and TOML files parse to a `dict` using only the stdlib.
- [ ] YAML parses when PyYAML is present (test via `importorskip`).
- [ ] Missing PyYAML on a `.yaml` input raises an actionable error naming the extra.
- [ ] Unknown extension and non-mapping root raise a located error.

## Blocked by

None - can start immediately.
