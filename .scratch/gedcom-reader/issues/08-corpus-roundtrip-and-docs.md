# 08 — Full-corpus round-trip property + docs

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

Close the loop. Add a property test that walks **every document fixture the writer's test suite builds** and asserts the round-trip oracle holds for all of them:

- Text oracle: `write(read(write(doc))) == write(doc)` byte-for-byte.
- Model oracle: `read(write(doc))` equals `doc` structurally, ignoring `xref_id`.

Then update the docs to match ADR-0005: `README.md` and `CONTEXT.md` move from "writer only / reading out of scope" to "writer plus a round-trip reader for our own output," keeping the general lenient-reader stance explicitly out of scope. Add a `Reading` section to the README showing `read_text` / `read_path`. Add a `CHANGELOG.md` entry under `Unreleased`.

## Acceptance criteria

- [ ] A single parametrized property test covers the full golden corpus; all documents satisfy both oracles.
- [ ] `README.md` documents the reader and its narrow scope; the "permanently out of scope" line is corrected to reference the lenient/third-party case only.
- [ ] `CONTEXT.md` reflects the reader (and adds any new domain term, e.g. the round-trip contract, if warranted).
- [ ] `CHANGELOG.md` has an `Unreleased` entry for the reader.
- [ ] `mise run check` is green.

## Blocked by

- 01–07.
