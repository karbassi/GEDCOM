# Loader tracer: header + individuals → GEDCOM

Status: done
Triage: ready-for-agent
Type: AFK

## What to build

The first end-to-end slice of `build_document(mapping) -> Document`: an authoring document with a `header` and `individuals` (names incl. structured pieces, sex, events, attributes, identifiers, restrictions) becomes a `Document` that serializes to a valid `HEAD`/`INDI`/`TRLR`. Wires into `build` so `gedcom build people.yaml -o out.ged` works for individuals-only trees. Enum mapping (case-insensitive names + spec strings + `_` extensions) and located `LoadError` land here.

## Acceptance criteria

- [ ] A minimal `{individuals: [{name: "Jane /Doe/", sex: F}]}` builds and emits a valid file (HEAD…INDI…TRLR).
- [ ] Names with `pieces`, multiple names, name `type`; events/attributes with dates and places; identifiers.
- [ ] Header fields (source product, language, copyright) authorable with defaults when omitted.
- [ ] Enum fields accept `female`/`F`; unknown value raises a located error naming the allowed set.

## Blocked by

- 02 (format reader), 03 (date dialect)
