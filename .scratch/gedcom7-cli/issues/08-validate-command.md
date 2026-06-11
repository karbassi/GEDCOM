# validate command

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

`gedcom7 validate <input>`: read and build the `Document`, run `validate(doc, strict=False)`, print issues (or "OK"), and exit nonzero when there are errors or the input fails to load/build. No output file is written.

## Acceptance criteria

- [ ] A clean document prints an OK message and exits 0.
- [ ] A document with validator issues prints them and exits 1.
- [ ] A load/build error (bad ref, bad date, bad enum) prints a located message and exits 2.

## Blocked by

- 04 (loader tracer)
