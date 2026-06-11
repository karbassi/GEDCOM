# CLI skeleton and packaging

Status: done
Triage: ready-for-agent
Type: AFK

## Parent

`.scratch/gedcom-cli/PRD.md`

## What to build

The `gedcom.cli` subpackage with an argparse-based `main(argv) -> int`, a `gedcom` console entry point, and `python -m gedcom`. Subcommands `build`, `validate`, `init` are wired with their flags and `--help`; `--version` prints the package version. This slice delivers the end-to-end shell — running `gedcom --version` and `gedcom --help` works — with the subcommand bodies delegating to functions filled in by later slices.

## Acceptance criteria

- [ ] `gedcom --version` prints the version and exits 0.
- [ ] `gedcom --help` and each subcommand's `--help` list the commands/flags.
- [ ] `main(["build", ...])` dispatches; unknown command / missing args exit 2.
- [ ] `python -m gedcom` runs the same entry point.
- [ ] `[project.scripts]` registers `gedcom = "gedcom.cli:main"`.

## Blocked by

None - can start immediately.
