# GEDCOM 7.0.18 Writer — Spec Map

A condensed, implementer-focused map of the [FamilySearch GEDCOM v7 specification](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html), scoped to what a **writer** (serializer) must emit. Source spec sections are cited as §x. This is the reference that the data model and serializer are built against.

> Scope: this library *writes* GEDCOM 7. It takes an in-memory genealogical model and emits a conformant `.ged` byte stream (and optionally a `.gdz` GEDZIP). Parsing/reading is out of scope.

---

## 1. The serialization model (§1)

GEDCOM 7 is a line-oriented, hierarchical text format. Every line encodes one structure (or pseudo-structure) and nests via an integer level.

### 1.1 Bytes & characters (§1.1)

- Output **MUST** be UTF-8. It is the only encoding allowed in 7.0.
- The stream **SHOULD** begin with a U+FEFF byte-order mark. The writer emits it by default.
- Files **SHOULD** use the `.ged` extension.
- **Banned characters** (MUST NOT appear anywhere): C0 controls except Tab/LF/CR (`%x00-08`, `%x0B-0C`, `%x0E-1F`), DEL (`%x7F`), C1 (`%x80-9F`), surrogates (`%xD800-DFFF`), and `%xFFFE-FFFF`. The writer must reject or sanitize payloads containing these.

### 1.2 The line grammar (§1.3)

```abnf
Line    = Level D [Xref D] Tag [D LineVal] EOL
Level   = "0" / nonzero *DIGIT
D       = %x20                            ; exactly one space, never more
Xref    = atsign 1*tagchar atsign         ; but not "@VOID@"
Tag     = stdTag / extTag
LineVal = pointer / lineStr
EOL     = %x0D [%x0A] / %x0A              ; CR-LF, CR, or LF
stdTag  = ucletter *tagchar               ; A-Z then [A-Z0-9_]*
extTag  = underscore 1*tagchar            ; _ then [A-Z0-9_]+
pointer = voidPtr / Xref
voidPtr = %s"@VOID@"
lineStr = (nonAt / atsign atsign) *nonEOL ; leading @ doubled
```

Writer-critical rules drawn from this grammar:

- **Level** encodes nesting. Level 0 is a record or record-like pseudo-structure (`HEAD`, `TRLR`). A line at level *x*>0 is a substructure of the nearest preceding line at level *x*−1.
- **Delimiter** between components is always exactly one space. Emitting two spaces after a tag means the second space is part of the line value.
- **Empty/absent payload**: `LineVal` never matches the empty string. A structure with no payload emits **no trailing space** after the tag (`1 MARR`, not `1 MARR `). Empty payload and missing payload are equivalent.
- **Escaping**: if a line string's **first** character is `@` (U+0040), it must be doubled (`@@`). `@` anywhere else is left alone. (This is narrower than pre-7.0, which doubled all `@`.)
- **Leading/trailing spaces** in payloads must be preserved verbatim.
- **EOL**: CR-LF, CR, or LF all valid; the same terminator **SHOULD** be used throughout a document. The writer picks one (default LF) and uses it everywhere.

### 1.3 Structures vs pseudo-structures (§1.2)

- A **structure** has a type (URI), an optional payload, and an ordered collection of substructures. It is either a **record** (level 0, no superstructure) or a **substructure** (exactly one superstructure).
- A structure **MUST** have either a non-empty payload or ≥1 substructure.
- **Pseudo-structures**: `HEAD`, `TRLR`, and `CONT` (line continuation). These need not have payload or substructures.

### 1.4 Cross-reference identifiers (§1.3)

- Form `@` + 1+ `tagchar` + `@`, excluding `@VOID@`. **MUST** be unique within the document.
- A record pointed to by any structure **MUST** carry an xref id; a record pointed to by nothing **MAY** carry one. Substructures and pseudo-structures **MUST NOT** carry one.
- Xref ids are document-local and transient — they **SHOULD NOT** be surfaced to users (so they must not be embedded in NOTE text as durable references).
- `@VOID@` is a valid pointer value anywhere a pointer is expected (a deliberate null pointer).

### 1.5 Multi-line payloads — `CONT` (§1.3)

- A payload containing line terminators is split on them. The first segment is the structure's own line value; each subsequent segment is a `CONT` pseudo-structure at level+1, immediately following, before any real substructure.
- `CONT` lines carry no xref. An empty payload line becomes a bare `CONT`.
- `CONC` does not exist in v7 (reserved, never emitted).

### 1.6 Header & trailer (§1.4)

- Every dataset: `0 HEAD` … records … `0 TRLR`. Ordering is mandatory.
- `HEAD` has no payload, **MUST** contain `GEDC` (with `GEDC.VERS` = the spec version string, e.g. `7.0`), and **SHOULD** contain `SCHMA` when any extension tags are used.
- `TRLR` has no payload and no substructures.

### 1.7 Extensions (§1.5) & removing data (§1.6)

- Extension tags match `extTag` (`_`-prefixed). Each must be declared in `HEAD.SCHMA` via a `TAG` substructure mapping the tag to a URI.
- Removing data: drop the structure; replace pointers to removed records with `@VOID@`; if a required substructure is removed, keep the structure but substitute `@VOID@` / an empty payload as appropriate.

---

## 2. Data types (§2) — how each payload serializes

| Type | URI | Serialization rule |
|---|---|---|
| Text | `xsd:string` | Any chars (minus banned); line breaks via `CONT`. |
| Integer | `xsd:nonNegativeInteger` | 1+ ASCII digits, non-negative; omit leading zeros. Negatives unsupported. |
| Enum | `g7:type-Enum` | A tag-like token (or, for standard enums, an integer). One of a per-structure permitted set; extension values are `_`-prefixed. |
| DateValue | `g7:type-Date` | `[calendar] [[day] month] year [epoch]`, optionally wrapped in `ABT/CAL/EST`, `BET…AND`, `AFT/BEF`, or a `FROM…TO` period. May be empty (with a substructure). |
| DateExact | `g7:type-Date#exact` | `day month year` in Gregorian only (e.g. `3 OCT 1937`). |
| DatePeriod | `g7:type-Date#period` | `FROM date [TO date]` or `TO date`; may be empty. |
| Time | `g7:type-Time` | `hh:mm[:ss[.fff]][Z]`, 24-hour; `Z` = UTC. No `24:00:00`, no leap seconds. |
| Age | `g7:type-Age` | optional `<`/`>` bound + duration like `35y 11m 8w 21d` (descending units, each optional but ordered). |
| List:Text / List:Enum | `g7:type-List#…` | Comma-separated; recommended delimiter is `", "`. No escaping for items containing commas or edge spaces. |
| PersonalName | `g7:type-Name` | Free text; `/` delimits the surname portion (`Joseph /Allen/`). No line breaks, no repeated spaces. |
| Language | `xsd:Language` | BCP 47 tag (e.g. `en`, `pt-BR`). |
| MediaType | `dcat:mediaType` | RFC 2045 `type/subtype[;params]` (e.g. `text/plain`, `image/jpeg`). |
| Special | `xsd:string` | Free text constrained per-structure (e.g. `PHON`, `IDNO`). |
| FilePath | `g7:type-FilePath` | A valid URL string: `http(s)`/`ftp`/`file` scheme, or a scheme-less relative local path (no leading `/`, no `..`, no `\`). Local files recommended under `media/`. |
| URI | `xsd:anyURI` | RFC 3986 URI-reference. |
| TagDef | `g7:type-TagDef` | `extTag SP URI` (used in `SCHMA.TAG`). |
| Latitude | `g7:type-Latitude` | `N`/`S` + 0–90 decimal degrees (e.g. `N18.150944`). |
| Longitude | `g7:type-Longitude` | `E`/`W` + 0–180 decimal degrees (e.g. `E168.150944`). |

### 2.1 Calendars & dates (§6)

- Calendars: `GREGORIAN` (default, omit when Gregorian), `JULIAN`, `FRENCH_R`, `HEBREW`, plus `_`-prefixed extensions.
- Months are calendar-specific stdTags: Gregorian/Julian `JAN…DEC`; `FRENCH_R` `VEND…COMP`; `HEBREW` `TSH…ELL`.
- Epochs: `BCE` permitted in Gregorian/Julian only; **no year 0** (1 BCE → 1 CE directly). `FRENCH_R`/`HEBREW` allow no epoch marker.
- A calendar tag applies only to the date immediately after it — so in `FROM x TO y` each date carries its own calendar; emit the calendar only for non-Gregorian dates.
- **No year-slash dual dates** (`1648/49` is forbidden). Emit one chosen date and put the original notation in a `PHRASE` substructure.
- Hebrew `ADR` (Adar I, leap years only) **SHOULD** become `ADS` in common years when the year is known.

---

## 3. The structure model (§3.2)

### 3.1 Document & records

```
0 HEAD          {1:1}   (first)
0 <record>      {0:M}   (any of the 7 record types below)
0 TRLR          {1:1}   (last)
```

Seven record types, each at level 0 with an xref id:

| Record | Tag | Required substructures | Notes |
|---|---|---|---|
| Family | `FAM` | — | `HUSB`/`WIFE` `{0:1}`, `CHIL` `{0:M}` **ordered by birth**; events, attributes, sealings. |
| Individual | `INDI` | — | names, `SEX` `{0:1}`, events, attributes, ordinances, `FAMC`/`FAMS` `{0:M}`. |
| Multimedia | `OBJE` | `FILE` `{1:M}`, each `FILE.FORM` | media references. |
| Repository | `REPO` | `NAME` | archive/library. |
| Shared note | `SNOTE` | — (payload is the note `Text` on the record line) | reusable note; `TRAN` needs `MIME` and/or `LANG`. |
| Source | `SOUR` | — | citable source; `DATA`, `AUTH`, `TITL`, repo citations. |
| Submitter | `SUBM` | `NAME` | contributor; `LANG` is `{0:M}` here. |

Header skeleton (required parts bolded): **`HEAD` → `GEDC` → `VERS`** required; `SCHMA`/`TAG` for extensions; optional `SOUR`, `DATE`/`TIME`, `SUBM` pointer, `LANG`, `PLAC.FORM` (required iff `HEAD.PLAC` present), `COPR`, `NOTE`.

### 3.2 Reusable substructure blocks

These named blocks are referenced by many records (each block is a natural dataclass):

- **ADDRESS_STRUCTURE** — `ADDR` (payload required, the full formatted address with `CONT` line breaks) + optional `CITY`/`STAE`/`POST`/`CTRY` etc. `ADR1`/`ADR2`/`ADR3` are **deprecated** (don't emit). `ADDR` payload is authoritative if it conflicts with subfields.
- **ASSOCIATION_STRUCTURE** — `ASSO @INDI@` (or `@VOID@` + `PHRASE`); `ROLE` **required** (enum), optional `ROLE.PHRASE`, notes, citations.
- **CHANGE_DATE** — `CHAN` → `DATE` (DateExact, required) → optional `TIME`; notes.
- **CREATION_DATE** — `CREA` → `DATE` (DateExact, required) → optional `TIME`. **Must not be modified on re-serialization** once set.
- **DATE_VALUE** — `DATE` (DateValue) + optional `TIME` (not with periods) + optional `PHRASE`.
- **EVENT_DETAIL** — shared event payload bag: date, place, address, contacts, `AGNC`/`RELI`/`CAUS`/`RESN`, `SDATE`, associations, notes, citations, media, `UID`.
- **PLACE_STRUCTURE** — `PLAC` (List:Text, small→large) + `FORM` (falls back to `HEAD.PLAC.FORM`), `LANG`, `TRAN` (each needs `LANG`), `MAP` (needs both `LATI`+`LONG`), `EXID`, notes.
- **PERSONAL_NAME_STRUCTURE** — `NAME` (PersonalName, required) + `TYPE` (enum) + name pieces + `TRAN` (each needs `LANG`) + notes/citations.
- **PERSONAL_NAME_PIECES** — `NPFX`/`GIVN`/`NICK`/`SPFX`/`SURN`/`NSFX`, all `{0:M}`; auxiliary to the authoritative `NAME` payload.
- **NOTE_STRUCTURE** — either `NOTE` (inline Text + `MIME`/`LANG`/`TRAN`) or `SNOTE @SNOTE@` (pointer). `NOTE.TRAN` needs `MIME` and/or `LANG`.
- **SOURCE_CITATION** — `SOUR @SOUR@` (or `@VOID@`) + `PAGE`, `DATA`, `EVEN`/`ROLE`, `QUAY` (enum `0`–`3`), media, notes.
- **SOURCE_REPOSITORY_CITATION** — `REPO @REPO@` + notes + `CALN` (call numbers, each with optional `MEDI`).
- **IDENTIFIER_STRUCTURE** — one of `REFN` (+optional `TYPE`), `UID`, or `EXID` (+`TYPE`; emitting `EXID` without `TYPE` is **deprecated**, becomes required in 8.0).
- **MULTIMEDIA_LINK** — `OBJE @OBJE@` + optional `CROP` (`TOP`/`LEFT`/`HEIGHT`/`WIDTH`) + `TITL`.
- **NON_EVENT_STRUCTURE** — `NO <eventEnum>` + optional `DATE` (DatePeriod) + notes/citations. Asserts an event did *not* occur.
- **CHANGE_DATE**/**CREATION_DATE** as above.

### 3.3 Events, attributes, ordinances (§3.3)

- **Events** (`BIRT`, `DEAT`, `MARR`, …): payload is `[Y|<NULL>]`. An event **asserts occurrence** only if it has a `DATE`, a `PLAC`, or a `Y` payload; otherwise it's inconclusive research notes. Generic `INDI.EVEN`/`FAM.EVEN` carry `Text` and **require** `TYPE`.
- **Attributes** (`OCCU`, `RESI`, `NCHI`, …): mere presence asserts the attribute applied — no date/place/`Y` needed. `IDNO` and generic `INDI.FACT`/`FAM.FACT` **require** `TYPE`. Payload types vary: `NCHI`/`NMR` are Integer; `IDNO`/`SSN` are Special; rest Text.
- **LDS ordinances** (`BAPL`, `CONL`, `ENDL`, `INIL`, `SLGC`, `SLGS`): distinct from the similarly-named events (`BAPL`≠`BAPM`, `CONL`≠`CONF`). `SLGS` is family-level; the rest individual-level. `SLGC` **requires** `FAMC`. `LDS_ORDINANCE_DETAIL.STAT` (enum) **requires** `DATE` when present; dates must be Gregorian, ≥1830.
- **Tag/URI collisions** the model must disambiguate by superstructure: `CENS` (INDI vs FAM), `NCHI` (INDI vs FAM), `RESI` (INDI vs FAM), `ADOP` (event vs `FAMC.ADOP` enum), `HUSB`/`WIFE` (FAM pointers vs ROLE/AGE enums).

---

## 4. Enumeration sets (§3.4)

The writer emits exactly these strings (extension values are `_`-prefixed). `OTHER` **SHOULD** be accompanied by a `PHRASE`.

- **SEX**: `M F X U`
- **RESN** (List): `CONFIDENTIAL LOCKED PRIVACY` (e.g. `1 RESN CONFIDENTIAL, LOCKED`; `PRIVACY` discouraged)
- **MEDI**: `AUDIO BOOK CARD ELECTRONIC FICHE FILM MAGAZINE MANUSCRIPT MAP NEWSPAPER PHOTO TOMBSTONE VIDEO OTHER`
- **PEDI**: `ADOPTED BIRTH FOSTER SEALING OTHER`
- **QUAY**: `0 1 2 3` (literal digit strings, no numeric meaning)
- **ROLE**: `CHIL CLERGY FATH FRIEND GODP HUSB MOTH MULTIPLE NGHBR OFFICIATOR PARENT SPOU WIFE WITN OTHER`
- **NAME-TYPE**: `AKA BIRTH IMMIGRANT MAIDEN MARRIED PROFESSIONAL OTHER`
- **FAMC-STAT**: `CHALLENGED DISPROVEN PROVEN`
- **ADOP**: `HUSB WIFE BOTH`
- **ord-STAT**: `BIC CANCELED CHILD DNS DNS_CAN STILLBORN` (current) + several deprecated (`COMPLETED`, `EXCLUDED`, `INFANT`, `PRE_1970`, `SUBMITTED`, `UNCLEARED`); respect the per-ordinance "applies to" constraints.
- **EVEN / EVENATTR**: event/attribute tag names used as enum values (with generic URIs for `CENS`/`NCHI`/`RESI`/`FACT`/`EVEN`).

---

## 5. Cross-cutting writer obligations

- **Ordering**: `HEAD` first / `TRLR` last; `GEDC` SHOULD be first in `HEAD`; `FAM.CHIL` **must** be birth-chronological; same-type substructures are preference-ordered (first = preferred); different-type substructures may be in any order.
- **Bidirectional integrity (MUST)**: `FAM.HUSB`/`FAM.WIFE` → that `INDI` must have a matching `FAMS`; `FAM.CHIL` → that `INDI` must have a matching `FAMC`.
- **No pointer cycles** between `OBJE`↔`SOUR` and `SNOTE`↔`SOUR`.
- **Uniqueness**: every xref id unique; every referenced pointer must resolve to a record in the document (or be `@VOID@`).
- **Deprecations to avoid emitting**: `ADR1/2/3`, `EXID` without `TYPE`, year-slash dual dates, deprecated `ord-STAT` values, `HEAD.SOUR.DATA`.
- **Required-substructure enforcement**: `OBJE.FILE`(+`FORM`), `REPO.NAME`, `SUBM.NAME`, `HEAD.GEDC.VERS`, `ASSO.ROLE`, `SLGC.FAMC`, `MAP.LATI`+`LONG`, `NAME.TRAN.LANG`, `PLAC.TRAN.LANG`, `(S)NOTE.TRAN` MIME/LANG, `STAT.DATE`, `TYPE` for `EVEN`/`FACT`/`IDNO`.

---

## 6. GEDZIP (`.gdz`) (§4)

Optional output: a ZIP archive containing `gedcom.ged` plus one entry per local-file `FilePath` payload, named by the (percent-decoded) path. Reserved names `META-INF/`, `MANIFEST.MF` must be avoided; a referenced local file literally named `gedcom.ged` must be renamed first. Internal separators are `/`; names are case-sensitive UTF-8. Recommended to compress text only.

---

## 7. Proposed Python architecture (to be stress-tested in `/grill-with-docs`)

This is the design hypothesis, not yet locked. It separates three concerns: an **in-memory model**, the **two-level encoding** (model → structure tree → text), and **validation**.

### 7.1 Layering

1. **`model/`** — `dataclasses` mirroring the spec's records and reusable substructure blocks (`Individual`, `Family`, `Multimedia`, `Repository`, `Source`, `SharedNote`, `Submitter`, `Header`; blocks like `PlaceStructure`, `SourceCitation`, `PersonalName`, `Address`, `EventDetail`, `Date`, `Age`, …). **Record types are mutable; value/datatype types are frozen** (ADR-0003). Records link to one another by **object reference**, not xref strings (ADR-0001).
2. **Datatype serializers** (`types.py`) — pure functions `Date → str`, `Age → str`, `Latitude → str`, list joining, etc. Each maps 1:1 to a §2 type.
3. **`gedcom_lines.py`** — the universal `Line(level, xref, tag, value)` primitive and the line-emitter that handles delimiters, the leading-`@` escape, `CONT` splitting, chosen EOL, and the BOM. This is the only place that knows the §1 grammar.
4. **`writer.py` / structure tree** — walks the model, allocates/validates xref ids, orders substructures per the rules, and produces a flat sequence of `Line`s that the line-emitter renders.
5. **`validation.py`** — enforces the cross-cutting obligations in §5 (required substructures, bidirectional integrity, cycle checks, uniqueness). Configurable strict/lenient.
6. **`gedzip.py`** — optional `.gdz` packaging (later slice).

### 7.2 Why this shape

- The `Line` primitive isolates every byte-level rule (escaping, `CONT`, EOL, banned chars) in one tested module, so record serializers stay declarative.
- Per-datatype pure functions are trivially unit-testable against the spec's ABNF examples and become the natural first TDD targets.
- Frozen dataclasses keep the public surface dependency-free and let consumers build models without our validation getting in the way until serialize-time.
- Validation is a separate pass so a "best effort" mode can warn-and-emit while a strict mode raises.

### 7.3 Resolved decisions (from `/grill-with-docs`)

| Decision | Resolution | Where |
|---|---|---|
| Model naming | **Domain words** (`Individual`, `Family`, …); wire tag is an internal encoding detail. | CONTEXT.md |
| Top-level aggregate | A **`Document`** owns Header + records + the xref namespace; it is the unit you serialize. | CONTEXT.md |
| Linking & xref ids | **Object references**; writer auto-assigns `@xref@` at serialize time (optional per-record override); bidirectional `FAMS`/`FAMC` integrity is **derived**. | ADR-0001 |
| Validation | **Two-tier**: value invariants at construction (via value types), document-level rules in a serialize-time pass. **Strict by default**, lenient opt-in. | ADR-0002 |
| Mutability | **Value types frozen, record types mutable** (to allow reference cycles like `BIRT.FAMC` ⇄ `CHIL`). | ADR-0003 |
| Enums | **Typed enums per set** + a `_`-prefixed extension escape hatch. | CONTEXT.md / model |
| Extensions (v1) | **Minimal**: extension enum values + auto-emitted `HEAD.SCHMA`; custom extension records/substructures **deferred** past v1. | PRD scope |
| Output API | `dumps(doc) -> str` convenience + `dump(doc, path_or_stream)` writing canonical UTF-8 bytes (BOM + chosen EOL); byte stream is authoritative. | model/writer |
```
