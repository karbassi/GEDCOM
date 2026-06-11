# A GEDCOM 7 reader, scoped to round-tripping our own output

The library gains a **reader**: a parser from GEDCOM 7 text (`.ged`) and GEDZIP (`.gdz`) back into the in-memory model. Its scope is deliberately narrow — it must faithfully parse **any document this library writes**, and nothing more is promised. The contract is a round-trip property: for every model the writer accepts, `read(write(model))` reconstructs an equal model, and `write(read(text))` reproduces byte-identical text. The reader is **strict only**: malformed input, unknown tags outside a declared `HEAD.SCHMA` extension, and values that violate the model's construction-time invariants are errors, not warnings.

This **reverses the writer-only scope** previously stated in `README.md` and `CONTEXT.md` ("Reading/parsing — permanently out of scope"). That earlier decision still holds for its real target — a lenient, real-world reader that ingests arbitrary third-party GEDCOM (legacy 5.5.1, messy exports, untrusted input). That remains out of scope and a non-goal. What changes is narrower: we now treat our own emitted format as a closed, well-formed language and provide its inverse.

## Why

Three things make this cheap and safe where a general parser would not be. First, the input is **well-formed by construction** — we are parsing a language we control, so the lenient/partial-parse machinery that dominates real-world GEDCOM parsing is unnecessary, and strict-only stays aligned with ADR-0002 rather than fighting it. Second, the foundation already exists: the §1.3 line grammar (`lines.py`), the typed target model, the spec-as-data registries (`registry/*.tsv`), and registry-driven validation are all reusable; the new work is an inverse of the explicit encoders in `serialize/`. Third, the round-trip property is a **self-checking oracle** — every model the existing test suite builds becomes a reader test for free, so correctness is measured against the writer, not against hand-written fixtures.

## Consequences

- **Strict-only, no lenient mode.** A reader that only consumes our output never needs to tolerate malformed input; adding lenient parsing later would be a separate decision with its own ADR.
- **Exact xref ids are not preserved by the writer (ADR-0001), so the round-trip equality is _model_ equality, not id equality.** `write → read → write` is byte-identical because re-serialization re-mints ids deterministically; `read → write` of our own output is byte-identical for the same reason. Equality is defined structurally, ignoring transient xref strings.
- **The reader inherits the model's eager validation.** Values that the value types reject at construction (a `Latitude` out of range, a malformed `Age`) surface as parse errors. This is intended.
- **Security posture is unchanged.** `SECURITY.md` still scopes out parsing untrusted, arbitrary GEDCOM. This reader's promise is bounded to our own output; feeding it hostile input is outside the contract. GEDZIP reading adds an unzip path that must still guard against zip-bomb / path-traversal entries even within that bounded promise.
- **Docs must be updated** to reflect the reversal: `README.md` and `CONTEXT.md` move from "writer only" to "writer, plus a round-trip reader for our own output."
