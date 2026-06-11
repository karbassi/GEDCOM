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
