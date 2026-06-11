# 01 — Walking skeleton: minimal valid document

Status: done
Type: HITL

## Parent

PRD: `.scratch/gedcom-writer/PRD.md`

## What to build

The end-to-end spine of the writer. A `Document` holding a `Header` with the required GEDCOM version, and no records, serializes to the minimal valid GEDCOM 7 file. This establishes the foundational module shapes — the `Line(level, xref, tag, value)` primitive and renderer, `model.Document`/`Header`, and the public `writer.dumps(document) -> str` plus `writer.dump(document, path_or_stream)` (UTF-8 bytes with a leading BOM and a chosen EOL, default LF). This is HITL: review the public API surface, module boundaries, and golden-test approach before the AFK slices fan out and commit to them.

## Acceptance criteria

- [ ] `dumps(Document(Header(gedcom_version="7.0")))` returns exactly `0 HEAD` / `1 GEDC` / `2 VERS 7.0` / `0 TRLR` joined by LF with a trailing newline.
- [ ] `dump(doc, path_or_stream)` writes UTF-8 bytes beginning with the U+FEFF BOM.
- [ ] The line terminator is selectable (LF default; CR-LF and CR supported) and applied to every line; `dumps` omits the BOM, `dump` includes it.
- [ ] `Line` renders level, optional xref, tag, and optional value with exactly one space between components and no trailing space when the value is absent.
- [ ] Golden-file test asserts the exact minimal-document bytes; unit tests cover `Line` rendering.
- [ ] `mise run check` passes (ruff, mypy strict, pytest).

## Blocked by

- None - can start immediately
