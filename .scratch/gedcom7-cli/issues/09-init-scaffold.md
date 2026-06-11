# init scaffold

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

`gedcom7 init`: print a commented starter authoring document to stdout (or `-o`), in YAML by default with `--format json|toml`. The template exercises the common fields (header, two individuals, a family, a source) so it doubles as runnable documentation: its output, fed back into `build`, produces a valid file.

## Acceptance criteria

- [ ] `gedcom7 init` prints a YAML template; `--format json|toml` switch formats.
- [ ] The emitted template re-parses and `build`s into a valid GEDCOM file.
- [ ] `-o` writes the template to a file.

## Blocked by

- 06 (remaining records) so the template can exercise the full surface
