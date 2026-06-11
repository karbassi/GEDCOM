# CLI skeleton and packaging

Status: done
Triage: ready-for-agent
Type: AFK

## Parent

`.scratch/gedcom7-cli/PRD.md`

## What to build

The `gedcom7.cli` subpackage with an argparse-based `main(argv) -> int`, a `gedcom7` console entry point, and `python -m gedcom7`. Subcommands `build`, `validate`, `init` are wired with their flags and `--help`; `--version` prints the package version. This slice delivers the end-to-end shell — running `gedcom7 --version` and `gedcom7 --help` works — with the subcommand bodies delegating to functions filled in by later slices.

## Acceptance criteria

- [ ] `gedcom7 --version` prints the version and exits 0.
- [ ] `gedcom7 --help` and each subcommand's `--help` list the commands/flags.
- [ ] `main(["build", ...])` dispatches; unknown command / missing args exit 2.
- [ ] `python -m gedcom7` runs the same entry point.
- [ ] `[project.scripts]` registers `gedcom7 = "gedcom7.cli:main"`.

## Blocked by

None - can start immediately.
