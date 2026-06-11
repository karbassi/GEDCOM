"""Structure forest → :class:`~gedcom.model.Document`.

Dispatches each level-0 structure to its decoder. Tracer-bullet scope
(slice 01) knows only ``HEAD`` and ``TRLR``; an unhandled level-0 tag is a
strict error (ADR-0005) until a later slice teaches the reader that record.
"""

from __future__ import annotations

from ..model import Document, Header
from ._header import parse_header
from ._tree import Node
from .errors import ParseError


def build_document(roots: list[Node]) -> Document:
    """Assemble a Document from its level-0 structure trees."""
    header: Header | None = None
    seen_trailer = False

    for node in roots:
        tag = node.tag
        if tag == "HEAD":
            if header is not None:
                raise ParseError("more than one HEAD", tag=tag)
            header = parse_header(node)
        elif tag == "TRLR":
            seen_trailer = True
        else:
            raise ParseError(f"unsupported top-level record: {tag}", tag=tag)

    if header is None:
        raise ParseError("document has no HEAD")
    if not seen_trailer:
        raise ParseError("document has no TRLR")

    return Document(header=header, records=[])
