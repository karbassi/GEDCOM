# 17 — Arbitrary (unregistered) extension structures

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md` (deferred from v1 "Out of Scope": custom extension records/substructures).

## What to build

A general mechanism for a consumer to attach a user-defined `_`-prefixed extension structure — its tag, payload, and a consumer-supplied URI — at the levels the spec permits, including nested extension substructures. The tag→URI mapping is declared in the auto-emitted `HEAD.SCHMA`. This complements the registry-alignment PRD's registered-only support (`.scratch/gedcom7-registry-alignment/issues/06`) by allowing any URI the consumer provides, rather than only registry-listed structures.

## Acceptance criteria

- [ ] A user-defined `_`-tag structure with a supplied URI and payload serializes to correct level/tag/value lines.
- [ ] Nested extension substructures under a standard or extension structure serialize at the right levels.
- [ ] Each distinct extension tag used contributes its tag→URI to `HEAD.SCHMA` exactly once.
- [ ] Validation accepts a well-formed extension structure (lenient) and flags a `_`-tag with no declared URI.
- [ ] Golden + unit tests for a record carrying a nested user-defined extension structure and its generated schema.

## Blocked by

- `.scratch/gedcom7-registry-alignment/issues/06` (registered extension structures) — establishes the extension-structure model this generalizes.
