# 03 — Core records: Individual + Family with pointer resolution

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-reader/PRD.md`

## What to build

Extend `parse/_records.py` to decode `INDI` and `FAM` records, and implement the **two-pass pointer resolution** the model needs (ADR-0001):

1. First pass — build every level-0 record shell and an `@xref@` → record index.
2. Second pass — resolve pointer payloads to object references: `FAM.HUSB`/`WIFE`/`CHIL` → `Individual`s, `INDI.FAMS`/`FAMC` → `Family`s. `@VOID@` resolves to the void pointer; any other unresolvable pointer is a `ParseError`.

Bidirectional integrity that the writer derives is read off the wire here, then re-derived identically on re-serialization, so the round-trip stays byte-identical.

## Acceptance criteria

- [ ] A document of several `Individual`s and `Family`s (spouses + children) round-trips byte-identically through `write → read → write`.
- [ ] Object references are restored: a parsed `Family.children[0]` is the same `Individual` object the document lists, not a copy.
- [ ] `@VOID@` pointers round-trip; a dangling non-void pointer raises `ParseError`.
- [ ] The parsed model equals the source model structurally (ignoring `xref_id`).
- [ ] Tests cover spouse/child wiring, `@VOID@`, and a dangling-pointer error.
- [ ] `mise run check` is green.

## Blocked by

- 01, 02.
