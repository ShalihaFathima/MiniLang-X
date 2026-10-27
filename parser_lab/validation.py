"""
MiniLang-X Parser Lab — Context-Free Grammar Validation and Diagnostics
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from parser_lab.grammar import (
    Grammar,
    Production,
    EPSILON,
    is_nonterminal_name,
)


@dataclass
class Diagnostic:
    """Diagnostic message for grammar issues."""
    severity: str  # "error" or "warning"
    message: str
    line: Optional[int] = None
    symbol: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
            "symbol": self.symbol,
        }


@dataclass
class ValidationResult:
    """Result of grammar validation."""
    valid: bool
    diagnostics: list[Diagnostic]
    grammar: Optional[Grammar] = None

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


class GrammarValidator:
    """Validates context-free grammars and generates actionable diagnostics."""

    @classmethod
    def validate(
        cls,
        grammar: Optional[Grammar],
        parse_diagnostics: Optional[Sequence[dict | Diagnostic]] = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []

        # Ingest parse-time diagnostics
        if parse_diagnostics:
            for item in parse_diagnostics:
                if isinstance(item, Diagnostic):
                    diagnostics.append(item)
                elif isinstance(item, dict):
                    diagnostics.append(
                        Diagnostic(
                            severity=item.get("severity", "error"),
                            message=item.get("message", "Syntax error"),
                            line=item.get("line"),
                            symbol=item.get("symbol"),
                        )
                    )

        if grammar is None or not grammar.productions:
            if not any(d.severity == "error" for d in diagnostics):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        message="Grammar is empty. Please enter at least one production rule.",
                        line=1,
                    )
                )
            return ValidationResult(valid=False, diagnostics=diagnostics, grammar=None)

        # 1. Validate Start Symbol
        if not grammar.start_symbol:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message="No start symbol defined or inferable for grammar.",
                    line=1,
                )
            )
        elif grammar.start_symbol not in grammar.nonterminals:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message=f"Invalid start symbol '{grammar.start_symbol}': not defined as a nonterminal.",
                    line=1,
                    symbol=grammar.start_symbol,
                )
            )

        # 2. Check for Epsilon mixed with other symbols
        for prod in grammar.productions:
            if len(prod.rhs) > 1 and EPSILON in prod.rhs:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        message=(
                            f"Epsilon '{EPSILON}' cannot be mixed with other symbols "
                            f"in alternative '{' '.join(prod.rhs)}'."
                        ),
                        line=prod.line,
                        symbol=EPSILON,
                    )
                )

        # 3. Check for Undefined Nonterminals
        # By convention, any symbol named like a nonterminal (capitalized or <...>)
        # on the RHS that has no corresponding production rule is flagged as undefined.
        known_nonterminals = set(grammar.nonterminals)
        reported_undefined: set[str] = set()

        for prod in grammar.productions:
            for sym in prod.rhs:
                if sym == EPSILON:
                    continue
                if is_nonterminal_name(sym) and sym not in known_nonterminals:
                    if sym not in reported_undefined:
                        reported_undefined.add(sym)
                        diagnostics.append(
                            Diagnostic(
                                severity="error",
                                message=(
                                    f"Undefined nonterminal '{sym}' referenced on right-hand side "
                                    f"without any production rules."
                                ),
                                line=prod.line,
                                symbol=sym,
                            )
                        )

        # 4. Check Duplicate Production Rules & Normalize
        seen_rules: set[tuple[str, tuple[str, ...]]] = set()
        deduped_productions: list[Production] = []
        for prod in grammar.productions:
            rule_key = (prod.lhs, prod.rhs)
            if rule_key in seen_rules:
                diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        message=f"Duplicate production rule '{prod}' detected and normalized.",
                        line=prod.line,
                        symbol=prod.lhs,
                    )
                )
            else:
                seen_rules.add(rule_key)
                deduped_productions.append(prod)

        # Update grammar with normalized productions
        grammar.productions = deduped_productions

        # 5. Check for Unreachable Nonterminals (Warning)
        if grammar.start_symbol in known_nonterminals:
            reachable = cls._compute_reachable_nonterminals(grammar)
            for nt in grammar.nonterminals:
                if nt not in reachable:
                    diagnostics.append(
                        Diagnostic(
                            severity="warning",
                            message=f"Nonterminal '{nt}' is unreachable from start symbol '{grammar.start_symbol}'.",
                            symbol=nt,
                        )
                    )

        is_valid = not any(d.severity == "error" for d in diagnostics)
        return ValidationResult(valid=is_valid, diagnostics=diagnostics, grammar=grammar)

    @staticmethod
    def _compute_reachable_nonterminals(grammar: Grammar) -> set[str]:
        """Performs BFS to discover all nonterminals reachable from the start symbol."""
        reachable: set[str] = set()
        if not grammar.start_symbol or grammar.start_symbol not in grammar.nonterminals:
            return reachable

        queue = [grammar.start_symbol]
        reachable.add(grammar.start_symbol)
        nt_set = set(grammar.nonterminals)

        while queue:
            curr = queue.pop(0)
            for prod in grammar.productions_for(curr):
                for sym in prod.rhs:
                    if sym in nt_set and sym not in reachable:
                        reachable.add(sym)
                        queue.append(sym)

        return reachable
