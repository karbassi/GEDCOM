"""Structure tree → :class:`~gedcom.model.Header`.

Tracer-bullet scope (slice 01): the minimal header the writer always emits —
``GEDC``/``VERS``. Later slices (04) extend this to the full header detail.
The inverse of :func:`gedcom.serialize._header.header_lines`.
"""

from __future__ import annotations

from ..model import Header
from ._tree import Node


def parse_header(node: Node) -> Header:
    """Build a Header from a ``HEAD`` structure node."""
    header = Header()
    gedc = node.child("GEDC")
    if gedc is not None:
        vers = gedc.child("VERS")
        if vers is not None and vers.value is not None:
            header.gedcom_version = vers.value
    return header
