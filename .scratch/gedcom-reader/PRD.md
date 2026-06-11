# PRD: gedcom — GEDCOM 7 reader (round-trip our own output)

Status: ready-for-agent

## Problem Statement

The library writes the full GEDCOM 7 standard record set but cannot read it back. That makes the writer unverifiable against its own output except by string comparison against hand-written golden files, and it leaves the project a one-way tool. A narrow reader — one that parses **any document this library writes** back into the model — closes both gaps without taking on the cost of a general-purpose, real-world GEDCOM parser.

This reverses the previously-documented "reading/parsing — permanently out of scope" stance, but only for the narrow case. See ADR-0005. The general lenient reader (legacy 5.5.1, messy third-party exports, untrusted input) remains out of scope.

## Solution

Add a **reader** — `parse/`, the structural inverse of `serialize/` — turning GEDCOM 7 text (`.ged`) and GEDZIP (`.gdz`) back into a `Document`. It is **strict only**: the input language is the one we emit, so malformed input, undeclared tags, and values that violate model construction invariants are errors.

The contract is a **round-trip property**, which is also the test oracle:

- **Text oracle (primary):** for our own emitted text `t`, `write(read(t)) == t` byte-for-byte.
- **Model oracle (secondary):** for any model `m` the writer accepts, `read(write(m))` equals `m` structurally, ignoring transient xref id strings (ADR-0001).

Every model the existing test suite already builds becomes a reader test for free. No new genealogical concepts are introduced; the reader produces the same model the rest of the library defines.

The work is sliced as tracer bullets: slice 01 drives the whole pipeline (tokenize → tree → model → re-serialize → compare) on the minimal HEAD+TRLR document and stands up the round-trip harness. Each later slice widens the subset that round-trips, end-to-end, until the full golden corpus passes.

## User Stories

1. As a developer, I want `gedcom.read_text(s)` to return a `Document` for any text the writer produced, so that I can load my own output back into the model.
2. As a developer, I want `gedcom.read_path(p)` to read both `.ged` and `.gdz`, so that reading mirrors the writer's two output forms.
3. As a developer, I want parsing malformed or undeclared input to raise a clear, located error (not silently degrade), so that the strict contract is trustworthy.
4. As a developer, I want every date/time/age/coordinate/enum the writer emits to parse back to an equal value, so that round-tripping is lossless at the value layer.
5. As a developer, I want cross-references (`FAMS`/`FAMC`, `HUSB`/`WIFE`/`CHIL`, citations, media links) resolved back to object references, so that the parsed model has the same shape the writer consumes.
6. As a developer, I want `HEAD.SCHMA`-declared extension structures and extension enum values to round-trip, so that extension output is not lossy.
7. As a maintainer, I want a property test asserting `write → read → write` is byte-identical across the entire golden corpus, so that the reader is verified against the writer, not against fresh fixtures.
8. As a maintainer, I want the reader to share the §1.3 grammar knowledge (`lines.py`) and the registries rather than re-encoding them, so that reader and writer cannot drift from the spec independently.
9. As a maintainer, I want `README.md` and `CONTEXT.md` updated to state the new scope (writer + round-trip reader), so that the docs match ADR-0005.

## Implementation Decisions

- **Module layout.** A new `src/gedcom/parse/` package, mirroring `serialize/`: `_tokenize.py` (physical lines → logical `Line`s, reassembling `CONT`), `_tree.py` (level stack → nested structure tree), `_records.py` / `_substructures.py` / `_header.py` (structure tree → model, inverse of the matching `serialize/` modules), and `_values.py` (text → value types, inverse of `types.py`). Public entry points `read_text`, `read_path` exported from `gedcom.__init__`.
- **Reuse, don't re-encode.** The `Line` dataclass and the §1.3 grammar live in `lines.py`; the tokenizer produces `Line`s and is the inverse of `render_line`. Tag→structure resolution and payload typing come from the same vendored registries (`_spec/`) the validator uses. The decoder dispatch mirrors the explicit encoder dispatch in `serialize/` (no magic), so the two stay legible side by side.
- **Strict only.** No lenient mode (ADR-0005). Errors raise a `ParseError` carrying line number and tag. Values that the model's value types reject at construction propagate as parse errors at the offending line.
- **Pointer resolution is two-pass.** First pass: build all level-0 records and an xref→record index. Second pass: resolve pointer payloads to object references; an unresolvable pointer (other than `@VOID@`) is a `ParseError`. Bidirectional links the writer derives (ADR-0001) are reconstructed from the wire, then re-derived identically on re-serialization.
- **Equality oracle.** Primary assertion is text-level (`write(read(t)) == t`); it sidesteps model `__eq__` subtleties and transient xrefs. Model equality is asserted where useful, comparing structurally and ignoring `xref_id`.
- **GEDZIP reading** unzips to read the GEDCOM payload and bundled media, guarding against path-traversal and zip-bomb entries even within the bounded "our own output" promise (SECURITY.md is otherwise unchanged).
- **Test placement.** Reader unit tests under `tests/` in the existing style; the corpus round-trip property test reuses the document fixtures the writer tests already build.

## Out of Scope

- Lenient parsing, error recovery, partial documents.
- GEDCOM 5.5.1 / legacy constructs (`CONC`, ANSEL, etc.).
- Reading arbitrary third-party GEDCOM not produced by this library.
- Untrusted-input hardening beyond the GEDZIP unzip guards (SECURITY.md stance unchanged).
