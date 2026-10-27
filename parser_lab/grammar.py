"""
MiniLang-X Parser Lab — Context-Free Grammar Representation and Parser
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

# Canonical symbol constants
EPSILON: str = "ε"
END_MARKER: str = "$"

EPSILON_ALIASES = frozenset({"ε", "eps", "epsilon", "EPS", "EPSILON"})

# Regex for splitting production LHS from RHS (supporting ->, →, ::=, =)
ARROW_PATTERN = re.compile(r"\s*(::=|->|→|=)\s*")

# Regex for tokenizing right-hand side symbols
# Matches quoted strings, identifiers/words, epsilon symbol, or single punctuation/operator characters
TOKEN_PATTERN = re.compile(
    r"""
    '(?:[^'\\]|\\.)*'      # Single-quoted string: e.g. '==' or 'id'
    |"(?:[^"\\]|\\.)*"     # Double-quoted string: e.g. "=="
    |[A-Za-z_][A-Za-z0-9_]* # Identifiers/keywords: e.g. E, Expr, id, num, eps
    |ε                     # Unicode epsilon
    |[^\s\w|]              # Single punctuation/operators: +, *, (, ), ;, etc.
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Production:
    """Represents a single grammar production rule: lhs -> rhs."""
    lhs: str
    rhs: tuple[str, ...]
    line: int = 1

    @property
    def is_epsilon(self) -> bool:
        """Returns True if the production rule directly derives epsilon."""
        return len(self.rhs) == 1 and self.rhs[0] == EPSILON

    def to_dict(self) -> dict:
        return {
            "lhs": self.lhs,
            "rhs": list(self.rhs),
            "line": self.line,
            "text": str(self),
            "is_epsilon": self.is_epsilon,
        }

    def __str__(self) -> str:
        rhs_str = " ".join(self.rhs) if self.rhs else EPSILON
        return f"{self.lhs} -> {rhs_str}"


def is_nonterminal_name(symbol: str) -> bool:
    """
    Determines if a symbol is canonically named as a nonterminal.
    By standard compiler convention: starts with uppercase letter or enclosed in <...>.
    """
    if not symbol:
        return False
    if symbol.startswith("<") and symbol.endswith(">") and len(symbol) > 2:
        return True
    return symbol[0].isupper()


def tokenize_alternative(alt_text: str) -> tuple[str, ...]:
    """
    Tokenizes a single right-hand side alternative into a tuple of grammar symbols.
    Handles space-separated and punctuated symbols, quotes, and epsilon aliases.
    """
    cleaned = alt_text.strip()
    if not cleaned:
        return (EPSILON,)

    raw_tokens = TOKEN_PATTERN.findall(cleaned)
    if not raw_tokens:
        return (EPSILON,)

    symbols: list[str] = []
    for token in raw_tokens:
        token = token.strip()
        if not token:
            continue
        # Check quoted terminals
        if (token.startswith("'") and token.endswith("'")) or (
            token.startswith('"') and token.endswith('"')
        ):
            unquoted = token[1:-1]
            symbols.append(unquoted if unquoted else EPSILON)
        elif token in EPSILON_ALIASES:
            symbols.append(EPSILON)
        else:
            symbols.append(token)

    if not symbols:
        return (EPSILON,)

    return tuple(symbols)


class Grammar:
    """
    Represents a Context-Free Grammar (V_N, V_T, P, S).
    """

    def __init__(
        self,
        productions: Sequence[Production],
        start_symbol: Optional[str] = None,
        raw_text: str = "",
    ) -> None:
        self.productions: list[Production] = list(productions)
        self.raw_text: str = raw_text

        # Extract nonterminals (preserving order of appearance on LHS)
        seen_nt: set[str] = set()
        nt_list: list[str] = []
        for prod in self.productions:
            if prod.lhs not in seen_nt:
                seen_nt.add(prod.lhs)
                nt_list.append(prod.lhs)
        self.nonterminals: list[str] = nt_list

        # Determine start symbol (explicit or default to first production's LHS)
        if start_symbol and start_symbol.strip():
            self.start_symbol: str = start_symbol.strip()
        elif self.nonterminals:
            self.start_symbol = self.nonterminals[0]
        else:
            self.start_symbol = ""

        # Extract terminals (all symbols on RHS that are not nonterminals and not epsilon/$)
        seen_term: set[str] = set()
        term_list: list[str] = []
        for prod in self.productions:
            for sym in prod.rhs:
                if sym != EPSILON and sym != END_MARKER and sym not in seen_nt:
                    if sym not in seen_term:
                        seen_term.add(sym)
                        term_list.append(sym)
        self.terminals: list[str] = term_list

    def productions_for(self, nonterminal: str) -> list[Production]:
        """Returns all productions with the specified nonterminal as LHS."""
        return [p for p in self.productions if p.lhs == nonterminal]

    def to_dict(self) -> dict:
        return {
            "start_symbol": self.start_symbol,
            "nonterminals": list(self.nonterminals),
            "terminals": list(self.terminals),
            "productions": [p.to_dict() for p in self.productions],
            "raw_text": self.raw_text,
        }

    def __repr__(self) -> str:
        return f"<Grammar start={self.start_symbol!r} nonterminals={self.nonterminals} terminals={self.terminals}>"


def parse_grammar_text(
    text: str, start_symbol: Optional[str] = None
) -> tuple[Optional[Grammar], list[dict]]:
    """
    Parses raw grammar text into Productions and builds a Grammar object.
    Collects any syntax/structural parsing diagnostics.
    """
    diagnostics: list[dict] = []
    productions: list[Production] = []

    lines = text.splitlines()

    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        # Ignore empty lines and comment lines
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        parts = ARROW_PATTERN.split(line, maxsplit=1)
        if len(parts) < 3:
            diagnostics.append({
                "severity": "error",
                "message": f"Malformed production line: missing derivation arrow ('->', '→', or '::=').",
                "line": line_idx,
                "symbol": None,
            })
            continue

        lhs_raw, _, rhs_raw = parts
        lhs = lhs_raw.strip()

        if not lhs:
            diagnostics.append({
                "severity": "error",
                "message": "Missing left-hand side nonterminal before derivation arrow.",
                "line": line_idx,
                "symbol": None,
            })
            continue

        # Check if LHS contains whitespace or multiple symbols
        lhs_tokens = lhs.split()
        if len(lhs_tokens) > 1:
            diagnostics.append({
                "severity": "error",
                "message": f"Context-free grammar LHS must be a single nonterminal, found multiple: '{lhs}'.",
                "line": line_idx,
                "symbol": lhs,
            })
            continue

        # Split multiple alternatives using '|'
        alternatives = rhs_raw.split("|")
        for alt_str in alternatives:
            rhs_tuple = tokenize_alternative(alt_str)
            productions.append(Production(lhs=lhs, rhs=rhs_tuple, line=line_idx))

    if not productions and not diagnostics:
        diagnostics.append({
            "severity": "error",
            "message": "Grammar is empty. Please enter at least one production rule.",
            "line": 1,
            "symbol": None,
        })
        return None, diagnostics

    grammar = Grammar(productions, start_symbol=start_symbol, raw_text=text)
    return grammar, diagnostics
