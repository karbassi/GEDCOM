"""Starter authoring documents for ``gedcom init``.

Each template describes the same small tree — a header, three individuals, a
family, and a cited source — so the output doubles as runnable documentation:
feeding it back into ``gedcom build`` produces a valid GEDCOM file.
"""

from __future__ import annotations

from .errors import LoadError

_YAML = """\
# gedcom authoring document. Build with: gedcom build this.yaml -o tree.ged
# Records link by handle (the `xref:` value); references may be written I1 or @I1@.

header:
  source: { product: My Genealogy, version: "1.0" }
  language: en
  copyright: "(c) 2024"

submitters:
  - xref: U1
    name: Pat Researcher

individuals:
  - xref: I1
    name: John /Smith/        # surname goes between slashes
    sex: M
    events:
      - { tag: BIRT, date: 1 JAN 1900, place: "Boston, Massachusetts, USA" }
      - { tag: DEAT, date: ABT 1970 }
    sources:
      - { source: S1, page: "p. 42" }

  - xref: I2
    name: Mary /Jones/
    sex: F
    events:
      - { tag: BIRT, date: 12 MAR 1905 }

  - xref: I3
    name: Sara /Smith/
    sex: F
    events:
      - { tag: BIRT, date: "1930" }

families:
  - xref: F1
    husband: I1
    wife: I2
    children: [I3]
    events:
      - { tag: MARR, date: 5 JUN 1925, place: "Boston, Massachusetts, USA" }

sources:
  - xref: S1
    title: Massachusetts Vital Records
    author: Commonwealth of Massachusetts
"""

_JSON = """\
{
  "header": {
    "source": { "product": "My Genealogy", "version": "1.0" },
    "language": "en",
    "copyright": "(c) 2024"
  },
  "submitters": [
    { "xref": "U1", "name": "Pat Researcher" }
  ],
  "individuals": [
    {
      "xref": "I1",
      "name": "John /Smith/",
      "sex": "M",
      "events": [
        { "tag": "BIRT", "date": "1 JAN 1900", "place": "Boston, Massachusetts, USA" },
        { "tag": "DEAT", "date": "ABT 1970" }
      ],
      "sources": [{ "source": "S1", "page": "p. 42" }]
    },
    {
      "xref": "I2",
      "name": "Mary /Jones/",
      "sex": "F",
      "events": [{ "tag": "BIRT", "date": "12 MAR 1905" }]
    },
    {
      "xref": "I3",
      "name": "Sara /Smith/",
      "sex": "F",
      "events": [{ "tag": "BIRT", "date": "1930" }]
    }
  ],
  "families": [
    {
      "xref": "F1",
      "husband": "I1",
      "wife": "I2",
      "children": ["I3"],
      "events": [{ "tag": "MARR", "date": "5 JUN 1925", "place": "Boston, Massachusetts, USA" }]
    }
  ],
  "sources": [
    {
      "xref": "S1",
      "title": "Massachusetts Vital Records",
      "author": "Commonwealth of Massachusetts"
    }
  ]
}
"""

_TEMPLATES = {"yaml": _YAML, "json": _JSON}


def scaffold(fmt: str) -> str:
    """Return a starter authoring document in ``fmt`` (``yaml``/``json``)."""
    try:
        return _TEMPLATES[fmt]
    except KeyError:
        raise LoadError(f"unknown init format {fmt!r}; use yaml or json") from None
