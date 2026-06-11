# 03 — Structure coverage audit

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-payload-conformance/PRD.md`

## What to build

A maximal-coverage `Document` fixture built in the test suite that exercises every standard construct the writer supports, serialized once. Resolve the emitted tags to standard structure URIs and compare against the standard, non-extension structure tags derived from `substructures.tsv`. Any standard structure with no serialization path must appear in an explicit, documented exclusion set; the audit fails if an un-excluded standard structure is missing. Produces a concrete coverage measure and guards against regressions.

## Acceptance criteria

- [ ] A maximal-coverage `Document` is constructed and serialized in the test suite.
- [ ] The audit derives the standard, non-extension structure-tag set from `substructures.tsv`.
- [ ] The emitted standard-tag set covers that set minus an explicit, documented exclusion list.
- [ ] Each excluded structure is recorded with a one-line reason (no silent omissions).
- [ ] The test fails if an un-excluded standard structure has no serialization path.

## Blocked by

- None - can start immediately.
