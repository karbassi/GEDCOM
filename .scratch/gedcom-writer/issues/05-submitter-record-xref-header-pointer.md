# 05 — Submitter record + xref allocation + Header pointer

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-writer/PRD.md`

## What to build

The first real record and the `xref` module. Add `Submitter` (`SUBM`, with required `NAME` and optional contact details) to the `Document`; implement deterministic, document-local `@xref@` allocation, object-identity pointer resolution, the `@VOID@` null pointer, and an optional per-record id override (ADR-0001). Wire `HEAD.SUBM` to point at a `Submitter` by object reference.

## Acceptance criteria

- [ ] A `Document` with one `Submitter` emits `0 @U1@ SUBM` / `1 NAME …` and a `HEAD` `1 SUBM @U1@` pointer resolved by object identity.
- [ ] xref ids are unique, deterministic for a given record order, and stable across runs.
- [ ] A per-record id override is honored; auto-assignment fills the rest without collision.
- [ ] `@VOID@` is emitted for a deliberate null pointer.
- [ ] Golden test for the submitter + header-pointer document; unit tests for allocation, resolution, override, and void.

## Blocked by

- #01 Walking skeleton: minimal valid document
