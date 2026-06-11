# Vendored GEDCOM 7 structure registry

Machine-readable spec tables copied verbatim from
[familysearch/GEDCOM](https://github.com/familysearch/GEDCOM/tree/main/extracted-files)
(`extracted-files/`), the authoritative source of truth for the GEDCOM 7
structure set.

- Upstream commit: `893dc5b422d75b96f91aa540be60c62c68337fdb`
- Files: `enumerationsets.tsv`, `enumerations.tsv`, `payloads.tsv`, `cardinalities.tsv`, `substructures.tsv`

These are used by `tests/test_registry.py` to assert the library never drifts
from the spec (enum members, event payload types). Re-vendor by re-copying
from upstream and updating the commit hash above.

## Terminology registry

Distilled from the live terminology registry
[FamilySearch/GEDCOM-registries](https://github.com/FamilySearch/GEDCOM-registries),
the canonical source for EXID type URIs, calendars/months, and registered
extension structures. The per-item YAMLs are distilled to TSV for offline,
stdlib-only test reads (one row per registry entry).

- Upstream commit: `079f5f61f3e2d3b22990da044c2db4ef75f08069`
- `exid-types.tsv` — the 14 registered `EXID`.`TYPE` authorities (`name`, `uri`, `label`), from `uri/exid-types/`.
- `calendars.tsv` — the 4 standard calendars (`standard_tag`, ordered `months`, permitted `epochs`), from `calendar/standard/`.
- `extension-structures.tsv` — the 14 registered `_`-prefixed extension structures (`name`, `tags`, `uri`, `label`, `payload`), from `structure/extension/`.
- `data-type-examples.tsv` — canonical worked-example payloads (`datatype`, `builder`, `gedcom`) for the value types, transcribed from the ABNF/example tables in `data-type/standard/`. Locks value formatting via `tests/test_data_type_lock.py`. (The spec's `24:00:00` end-of-day Time is intentionally omitted: this writer caps the hour at 23.)

These lock the library's `ExidType`, calendar month/epoch tables, and
registered-extension set against the registry. Re-vendor by re-running the
distillation against a newer commit and updating the hash above.
