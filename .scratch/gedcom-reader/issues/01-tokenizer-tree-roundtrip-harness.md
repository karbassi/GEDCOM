# 01 — Tracer bullet: tokenizer, tree, and the round-trip harness

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

The thinnest end-to-end vertical slice that proves the whole reader pipeline and stands up the test oracle. Create `src/gedcom/parse/` with:

- `_tokenize.py` — physical line strings → logical `Line`s (`gedcom.lines.Line`), the inverse of `render_line`: split level / optional `@xref@` / tag / value, reassemble `CONT` continuations into a single value, undo the leading-`@@` escape, and reject input that violates the §1.3 grammar with a located `ParseError`.
- `_tree.py` — a flat `Line` sequence → a nested structure tree using the level stack (each line's children are the deeper-level lines that follow it).
- `_header.py` + `_records.py` — minimal: reconstruct a `Document` carrying only a `Header` (and the implicit `TRLR`) from the smallest document the writer emits.
- `errors.py` — `ParseError(message, *, line=None, tag=None)`.
- Public `read_text(text: str) -> Document` exported from `gedcom.__init__`.

Establish the **round-trip harness** as a reusable test helper: given a `Document`, assert `write(read(write(doc))) == write(doc)` byte-for-byte.

## Acceptance criteria

- [ ] `read_text(write(Document(Header(...))))` returns a `Document` whose re-serialization is byte-identical to the input.
- [ ] The tokenizer round-trips `CONT` multi-line values and leading-`@` escapes (inverse of `render_line`).
- [ ] Malformed lines (bad level, missing tag) raise `ParseError` citing the line number.
- [ ] `tests/test_parse_roundtrip.py` houses the reusable round-trip helper and the minimal HEAD+TRLR case.
- [ ] `mise run check` is green (ruff, mypy --strict, pytest).

## Blocked by

- None — this is the tracer bullet.
