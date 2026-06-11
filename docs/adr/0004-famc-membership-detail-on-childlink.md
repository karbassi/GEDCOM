# FAMC membership detail lives on a ChildLink in Family.children

`INDI.FAMC` may carry per-membership detail — `PEDI` (pedigree) and `STAT` (child-to-family status), each with an optional `PHRASE`. But `FAMS`/`FAMC` are *derived* by the writer (ADR-0001): an `Individual` stores no family links, so there was no place to hang that detail. We attach it to a `ChildLink` entry within `Family.children` (used in place of a bare `Individual` when detail is needed); the writer emits the detail on the derived `INDI.FAMC` line. We chose this over storing the detail child-side (a `child_memberships` list on `Individual`) because that would make the caller reference the family from *both* sides — the `Family.children` list and the individual's membership list — which is exactly the dual-maintenance ADR-0001 exists to prevent. Keeping the family as the single source of the child↔family pair preserves that invariant while still emitting the detail where the spec puts it (under `INDI`).

## Consequences

- `Family.children` accepts `Individual | ChildLink | VoidPointer`; a `ChildLink` wraps the child plus its `PEDI`/`STAT` detail. Bare `Individual` entries are unchanged, so existing documents are unaffected.
- The derived-integrity guarantee is intact: `ChildLink` still produces the `FAM.CHIL` pointer and the matching derived `INDI.FAMC`; the detail only augments the latter.
- Event-level `FAMC` (`BIRT`/`CHR`/`ADOP`, with `ADOP.FAMC.ADOP`) is a separate concern — it is an explicit `FAMC` pointer inside an event's `EventDetail`, not a derived link, and carries no ADR-0001 tension.
