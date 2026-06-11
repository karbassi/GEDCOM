"""Registered `_`-prefixed extension structures (registry ``structure/extension``).

The registry's extension set is a third-party grab-bag, so this module supports
only the entries that map a single ``_``-prefixed tag to a single authoritative
URI. Deliberately excluded (documented, not silent):

- ``_CENR`` — registered twice with conflicting URIs (no unambiguous mapping).
- Seven entries (``Ancestry_PUBL_*``, ``MagiKey_FATH``/``MOTH``/``CENR_*``)
  register no ``_``-tag of their own.

Arbitrary, *unregistered* extension structures (a user-supplied tag + URI) are a
separate, broader feature (v1 issue #17) layered on top of this model.
"""

from __future__ import annotations

import csv
from functools import cache
from importlib import resources


@cache
def registered_extension_uris() -> dict[str, str]:
    """Map each supported registered extension tag to its authoritative URI."""
    source = resources.files("gedcom7._spec").joinpath("extension-structures.tsv")
    by_tag: dict[str, set[str]] = {}
    with resources.as_file(source) as path, path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            tags = row["tags"].split(",") if row["tags"] else []
            for tag in tags:
                by_tag.setdefault(tag, set()).add(row["uri"])
    return {tag: next(iter(uris)) for tag, uris in by_tag.items() if len(uris) == 1}
