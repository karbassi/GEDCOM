# Two-tier validation, strict by default

Validation is split in two. **Value-level invariants** are enforced at object construction by the value types themselves (a `Latitude` cannot hold a value outside 0–90; an `Age` cannot be malformed) plus dataclass `__post_init__` checks. **Document-level rules** — required substructures, bidirectional `FAMS`/`FAMC` integrity, xref uniqueness, forbidden `OBJE`↔`SOUR`/`SNOTE`↔`SOUR` cycles, deprecation warnings — are enforced in a dedicated serialize-time pass, because they can only be checked once the object graph is complete. The serialize pass defaults to **strict** (raise on violation); a **lenient** mode (warn and emit best-effort output) is opt-in.

## Why

Cross-record rules cannot run at construction time because a `Document` is assembled incrementally and references may be added in any order. Strict-by-default keeps malformed files from being produced silently; lenient mode exists because real genealogical data is frequently incomplete and some users need best-effort output over a hard failure.
