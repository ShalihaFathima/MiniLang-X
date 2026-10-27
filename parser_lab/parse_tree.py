"""
MiniLang-X Parser Lab — Parse Tree Representation
Provides hierarchical parse tree nodes for successful parsing outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParseTreeNode:
    """Represents a node in a concrete parse tree."""
    symbol: str
    is_terminal: bool = False
    children: list[ParseTreeNode] = field(default_factory=list)

    def add_child(self, child: ParseTreeNode) -> None:
        self.children.append(child)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "label": self.symbol,
            "is_terminal": self.is_terminal,
            "children": [c.to_dict() for c in self.children],
        }

    def __repr__(self) -> str:
        if self.is_terminal:
            return f"Leaf({self.symbol})"
        return f"Node({self.symbol}, children={len(self.children)})"
