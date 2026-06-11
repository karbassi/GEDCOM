# Object references with auto-assigned cross-reference ids

The model links records by Python object reference (e.g. `Family.husband` is an `Individual`), not by `@xref@` string. The writer mints document-local cross-reference ids at serialize time, resolving pointers by object identity; a record may optionally pin a preferred id. We chose this over caller-assigned id strings because the spec defines xref ids as transient, document-local, and not user-facing (§1.3), so ownership belongs in the serialization layer — and object-identity linking lets the writer **derive** bidirectional integrity (auto-emitting matching `FAMS`/`FAMC`, `CHIL`/`FAMC` pairs) rather than requiring the caller to maintain both sides and risk dangling pointers.

## Consequences

- The `Document` aggregate owns the xref namespace; ids are assigned deterministically (stable for a given record ordering) so output diffs are meaningful.
- Round-tripping exact original ids is not a goal; consumers who need specific ids use the per-record override.
- The writer must detect reference cycles where the format forbids them (`OBJE`↔`SOUR`, `SNOTE`↔`SOUR`) and reject unresolvable references to records not in the Document.
