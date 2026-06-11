# 09 — Events + attributes + non-events

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-writer/PRD.md`

## What to build

Individual and family event structures (`BIRT`, `DEAT`, `MARR`, … with `[Y|<NULL>]` payload and occurrence semantics), attribute structures (presence asserts; payload types per spec — Integer for `NCHI`/`NMR`, Special for `IDNO`/`SSN`, else Text), the generic `INDI.EVEN`/`FAM.EVEN`/`INDI.FACT`/`FAM.FACT` and `IDNO` requiring `TYPE`, the shared `EVENT_DETAIL`/`DATE_VALUE` bag (date, place, age where applicable, agency/cause/etc.), and the `NO` non-event structure. Disambiguate `CENS`/`NCHI`/`RESI` by superstructure (INDI vs FAM).

## Acceptance criteria

- [ ] An event with a `DATE`, `PLAC`, or `Y` payload asserts occurrence; one with none is inconclusive (no `Y` emitted).
- [ ] Attributes serialize on presence; `EVEN`/`FACT`/`IDNO` without `TYPE` are rejected in strict mode.
- [ ] `EVENT_DETAIL` substructures (date, place, age, agency/cause, etc.) serialize under events.
- [ ] `NO <event>` with optional `DATE` (DatePeriod) asserts non-occurrence.
- [ ] Golden tests for an individual with birth/death events and an occupation attribute; unit tests for occurrence semantics and `TYPE` enforcement.

## Blocked by

- #03 Data types + calendars
- #06 Individual + Personal Name
- #07 Family + children birth-order + derived integrity
