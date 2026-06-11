# Frozen value types, mutable record types

Value/datatype objects (`Date`, `Age`, `Latitude`, `Longitude`, `PersonalName` and its pieces, etc.) are frozen dataclasses; record objects (`Individual`, `Family`, `Multimedia`, `Source`, `Repository`, `SharedNote`, `Submitter`, `Header`) are mutable. This deviates from the original "all frozen" sketch in the spec map (§7).

## Why

The object-reference model (ADR-0001) admits reference cycles that the format requires — e.g. an `Individual`'s `BIRT.FAMC` points to a `Family` whose `CHIL` lists that same `Individual`. Frozen records cannot express a cycle, since each object would need the other to exist at construction. Making records mutable lets references be wired after construction; keeping value types frozen preserves the construction-time invariant guarantees from ADR-0002 (a `Latitude` can never be mutated out of range) where no cycle exists to prevent it.
