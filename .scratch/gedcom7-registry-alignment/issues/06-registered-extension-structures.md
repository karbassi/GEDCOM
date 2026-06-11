# 06 — Registered extension structures

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom7-registry-alignment/PRD.md`

## What to build

A bounded model representation for a *registered* `_`-prefixed extension structure (its tag, payload, and authoritative registry URI), attachable where the registry permits it. Serialize it as the corresponding `_`-tag line(s) and contribute its tag→URI to the auto-emitted `HEAD.SCHMA`, reusing the schema-collection path from the v1 PRD's issue #15. Only structures present in the vendored registered-extension set (`structure/extension`) are accepted; arbitrary user-defined tags are rejected (out of scope per the PRD).

## Acceptance criteria

- [ ] A registered extension structure can be attached to a record and serializes to its `_`-tag line(s).
- [ ] Its tag→URI is auto-declared in `HEAD.SCHMA` using the authoritative registry URI.
- [ ] An unregistered `_`-tag is rejected (registered-only).
- [ ] A drift test asserts our supported registered-extension set and URIs match the vendored `structure/extension`.
- [ ] Golden + unit tests for a record carrying a registered extension structure and its generated schema.

## Blocked by

- #01 Vendor registry data + provenance
- v1 PRD #15 (extension enum values + auto-SCHMA) — reuses the schema-collection path
