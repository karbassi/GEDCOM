# 03 — Calendar/month/epoch registry lock

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-registry-alignment/PRD.md`

## What to build

Drift-lock our in-code calendar definitions to the vendored registry: each calendar's **ordered** month list and its permitted **epochs**. Keep the in-code definitions as the runtime source; add a test that verifies month tokens, their order, and the permitted-epoch set against `calendar/standard`. Fix epoch handling so `BCE` is emitted only for calendars that permit an epoch (Gregorian, Julian) and never for those that don't (French Republican, Hebrew per the registry).

## Acceptance criteria

- [ ] A drift test asserts each calendar's ordered months and permitted epochs match the vendored `calendar/standard` data.
- [ ] Non-Gregorian dates serialize correct month tokens in correct positions (month number → right token) for all four calendars.
- [ ] `BCE` is emitted only where the calendar's `epochs` permit it; an epoch on a calendar that forbids it is rejected/never emitted.
- [ ] Golden + unit tests covering a date in each non-Gregorian calendar and the epoch rules.

## Blocked by

- #01 Vendor registry data + provenance
