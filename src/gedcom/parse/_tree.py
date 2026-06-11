"""Flat logical lines → a nested structure tree.

Uses the level as the only nesting signal (§1.3): a line is a child of the
most recent line one level shallower. The reader's structure decoders walk
this tree; the tokenizer's ``CONT`` folding means values are already whole by
the time a :class:`Node` is built.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from ..lines import Line
from .errors import ParseError


@dataclass
class Node:
    """A structure line plus its directly-nested child structures."""

    line: Line
    children: list[Node] = field(default_factory=list)

    @property
    def tag(self) -> str:
        return self.line.tag

    @property
    def value(self) -> str | None:
        return self.line.value

    def child(self, tag: str) -> Node | None:
        """The first child with ``tag``, or ``None``."""
        return next((c for c in self.children if c.tag == tag), None)

    def all(self, tag: str) -> list[Node]:
        """Every direct child with ``tag``, in order."""
        return [c for c in self.children if c.tag == tag]

    def text(self, tag: str) -> str | None:
        """The value of the first child with ``tag``, or ``None``."""
        child = self.child(tag)
        return child.value if child is not None else None


def build_tree(lines: Iterable[Line]) -> list[Node]:
    """Assemble logical lines into a forest of level-0 structure trees."""
    roots: list[Node] = []
    stack: list[Node] = []

    for line in lines:
        node = Node(line)
        if line.level == 0:
            roots.append(node)
            stack = [node]
            continue
        if not stack:
            raise ParseError("first line is not at level 0", tag=line.tag)
        if line.level > len(stack):
            raise ParseError(
                f"line level {line.level} skips a level (expected <= {len(stack)})",
                tag=line.tag,
            )
        del stack[line.level :]
        stack[-1].children.append(node)
        stack.append(node)

    return roots
