# GEDCOM

A Python library that **writes** (serializes) an in-memory genealogical model to the FamilySearch GEDCOM 7.0.18 text format (`.ged`) and optionally to GEDZIP (`.gdz`). Reading/parsing is out of scope.

## Language

The model speaks in **domain words**, not GEDCOM tags. Each record concept maps to a fixed wire tag, but the tag is an encoding detail owned by the serialization layer — it never appears in public class names.

### Records

**Individual**:
A person. Wire tag `INDI`.
_Avoid_: Person, INDI (in public API names)

**Family**:
A family unit linking spouses and children. Wire tag `FAM`.
_Avoid_: FAM, marriage, household

**Multimedia**:
A record referencing one or more external media files. Wire tag `OBJE`.
_Avoid_: Media, Object, OBJE, file (a Multimedia *contains* file references)

**Source**:
A citable source of genealogical information. Wire tag `SOUR`.
_Avoid_: Citation (a **Source Citation** points *at* a Source; they are distinct), SOUR

**Repository**:
An archive or library that holds Sources. Wire tag `REPO`.
_Avoid_: Archive, REPO

**Shared Note**:
A reusable note record that multiple structures can point to. Wire tag `SNOTE`.
_Avoid_: Note (an inline **Note** is a different, non-record concept), SNOTE

**Submitter**:
The contributor of data in the document. Wire tag `SUBM`.
_Avoid_: Author, contributor, user, SUBM

**Header**:
The document metadata pseudo-record that opens every file. Wire tag `HEAD`.

### Core encoding concepts

**Document**:
The top-level aggregate: a Header plus a collection of records, owning the cross-reference id namespace. The unit you build and hand to the writer. Wire form is `HEAD` … records … `TRLR`.
_Avoid_: Dataset (the *byte stream*), file, tree

**Line**:
The atomic unit of GEDCOM output: a level, optional cross-reference id, tag, optional value, and terminator. The serialization primitive.

**Cross-reference id** (xref):
A document-local `@…@` handle uniquely identifying a record so other structures can point to it. Transient — never shown to users.

**Pointer**:
A line value that references a record by its cross-reference id (or the null `@VOID@`).

**Substructure block**:
A reusable named cluster of substructures (e.g. Place Structure, Source Citation, Personal Name, Address, Event Detail) that several records embed.

**Inline Note** vs **Shared Note**:
An inline **Note** carries its text directly on a `NOTE` line under its owner. A **Shared Note** is a standalone record (`SNOTE`) pointed to by reference. Both are exposed, but they are distinct concepts.

## Relationships

- A document is a **Header**, then zero or more records, then a trailer.
- A **Family** points to **Individual**s as spouses (`HUSB`/`WIFE`) and children (`CHIL`, ordered by birth); each such **Individual** must point back via `FAMS`/`FAMC` (bidirectional integrity).
- A **Source Citation** points to a **Source**; a **Source** may cite **Repository**s via repository citations.
- Any record may carry **Multimedia** links, **Note**s / **Shared Note** pointers, and **Source Citation**s.

## Flagged ambiguities

- "Note" was overloaded: resolved into **Inline Note** (text on a `NOTE` line) vs **Shared Note** (the `SNOTE` record). Distinct concepts.
- "Source" vs "Citation": a **Source** is the record; a **Source Citation** is a reference to it from another structure. Kept separate.
