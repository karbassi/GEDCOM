# 02 — Line-grammar completeness

Status: needs-triage
Type: AFK

## Parent

PRD: `.scratch/gedcom7-writer/PRD.md`

## What to build

Extend the `lines` layer to fully honor the §1.3 byte grammar: split any payload containing line breaks into `CONT` continuation pseudo-structures at level+1; double a leading `@` in a line string; reject banned control characters; preserve leading/trailing spaces; support arbitrary nesting depth. Demonstrate end-to-end via Header free-text fields (`COPR` and an inline `NOTE`) carrying multi-line text.

## Acceptance criteria

- [ ] A payload with embedded newlines emits a first-line value plus one `CONT` line per subsequent segment, including a bare `CONT` for blank lines.
- [ ] A line string whose first character is `@` is emitted doubled (`@@…`); `@` elsewhere is left untouched.
- [ ] Banned characters (C0 except tab/LF/CR, DEL, C1, surrogates, U+FFFE/U+FFFF) raise a clear error in strict mode (per ADR-0002).
- [ ] Leading and trailing spaces in payloads are preserved exactly.
- [ ] Golden test: a Header with a 3-line `COPR` and a `NOTE` whose payload begins with `@`.
- [ ] Unit tests for CONT splitting, leading-`@` escaping, and banned-character rejection.

## Blocked by

- #01 Walking skeleton: minimal valid document
