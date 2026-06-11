# Date dialect parser

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

A deep `parse_date` / `parse_date_exact` module mapping the friendly date dialect to the existing value types: plain `CalendarDate` (`1 JAN 1900`, `JAN 1900`, `1900`, BCE), `ApproxDate` (`ABT`/`CAL`/`EST`), `DateRange` (`BET…AND`, `AFT`, `BEF`), `DatePeriod` (`FROM…TO`, `FROM`, `TO`), the four calendars by leading keyword, and native `date`/`datetime` values.

## Acceptance criteria

- [ ] Every head (`ABT`/`CAL`/`EST`/`BET…AND`/`AFT`/`BEF`/`FROM…TO`) maps to the right value type, asserted by re-emitted GEDCOM string.
- [ ] Julian/French/Hebrew calendars by leading keyword; Gregorian default.
- [ ] Native `date`/`datetime` accepted for both date and exact-date positions.
- [ ] Malformed strings raise a located error.

## Blocked by

None - can start immediately.
