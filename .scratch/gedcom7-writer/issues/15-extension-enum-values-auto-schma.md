# 15 — Extension enum values + auto-emitted HEAD.SCHMA

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

Collect every `_`-prefixed extension tag actually used in a `Document` (today, via extension enum values) and emit a conformant `HEAD.SCHMA` block declaring each as a `TAG` mapping to its URI. No file should use an extension tag without a corresponding `SCHMA` declaration. Custom extension records/substructures remain out of scope for v1.

## Acceptance criteria

- [ ] A document using a `_`-extension enum value auto-emits a `HEAD.SCHMA` block with a matching `TAG` line mapping the tag to its URI.
- [ ] No `SCHMA` is emitted when no extension tags are used.
- [ ] Golden + unit tests for a document with an extension enum value and its auto-generated schema.

## Blocked by

- #04 Typed enums + extension escape hatch
