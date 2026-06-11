# 02 — EXID type URI constants (ExidType)

Status: done
Type: AFK

## Parent

PRD: `.scratch/gedcom-registry-alignment/PRD.md`

## What to build

A typed `ExidType` vocabulary whose 14 members carry the exact registry `uri` for each well-known authority (FindAGrave, BillionGraves, WikiTree, FamilySearch Memory/Person/Place/Source/User, AFN, RFN, RIN, GOV-ID). The `Identifier` model's EXID `type` accepts an `ExidType` **or** a raw URI string (escape hatch for unregistered authorities). Serialization emits the URI as the `EXID`/`TYPE` payload. End-to-end: `Identifier("EXID", value, type=ExidType.FIND_A_GRAVE_MEMORIAL)` → correct bytes. Additive — existing string usage keeps working.

## Acceptance criteria

- [ ] `ExidType` exposes the 14 registered authorities, each value equal to the registry URI verbatim.
- [ ] An `Identifier` of kind `EXID` with an `ExidType` emits `EXID` + `TYPE <uri>`; a raw-string type still works.
- [ ] A drift test fails if `ExidType` (members or URIs) diverges from the vendored `uri/exid-types`.
- [ ] Golden + unit tests for an EXID identifier carrying an `ExidType`.

## Blocked by

- #01 Vendor registry data + provenance
