"""
MiniLang-X Parser Lab — FIRST and FOLLOW Set Iterative Computation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from parser_lab.grammar import (
    Grammar,
    EPSILON,
    END_MARKER,
)


def sorted_symbols(symbols: set[str]) -> list[str]:
    """Sorts grammar symbols deterministically for display and testing."""
    # Deterministic sort: terminals/identifiers alphabetically, with '$' and 'ε' consistently positioned
    return sorted(symbols, key=lambda s: (s == END_MARKER, s == EPSILON, s))


@dataclass
class FirstFollowResult:
    """Container for computed FIRST and FOLLOW sets."""
    first: dict[str, list[str]]
    follow: dict[str, list[str]]
    nullable: dict[str, bool]

    def to_dict(self) -> dict:
        return {
            "first": self.first,
            "follow": self.follow,
            "nullable": self.nullable,
        }


class FirstFollowCalculator:
    """
    Computes FIRST and FOLLOW sets for a context-free grammar using
    iterative fixed-point algorithms.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.terminals = set(grammar.terminals)
        self.nonterminals = set(grammar.nonterminals)

    def compute(self) -> FirstFollowResult:
        """Runs the complete FIRST and FOLLOW set computation."""
        raw_first = self.compute_first()
        raw_follow = self.compute_follow(raw_first)

        nullable_map = {
            nt: (EPSILON in raw_first.get(nt, set()))
            for nt in self.grammar.nonterminals
        }

        formatted_first = {
            nt: sorted_symbols(raw_first.get(nt, set()))
            for nt in self.grammar.nonterminals
        }

        formatted_follow = {
            nt: sorted_symbols(raw_follow.get(nt, set()))
            for nt in self.grammar.nonterminals
        }

        return FirstFollowResult(
            first=formatted_first,
            follow=formatted_follow,
            nullable=nullable_map,
        )

    def first_of_sequence(
        self,
        sequence: Sequence[str],
        first_sets: dict[str, set[str]],
    ) -> set[str]:
        r"""
        Computes FIRST(X_1 X_2 ... X_k) for a sequence of grammar symbols.

        Rules:
        1. If sequence is empty, FIRST is {ε}.
        2. Scan symbols left to right:
           - Add FIRST(X_i) \ {ε} to result.
           - If X_i is not nullable (ε ∉ FIRST(X_i)), stop scanning.
        3. If all symbols in sequence are nullable, add ε to result.
        """
        if not sequence:
            return {EPSILON}

        result: set[str] = set()
        all_nullable = True

        for sym in sequence:
            if sym == EPSILON:
                continue

            if sym in self.terminals or sym == END_MARKER:
                result.add(sym)
                all_nullable = False
                break
            elif sym in first_sets:
                sym_first = first_sets[sym]
                result.update(sym_first - {EPSILON})
                if EPSILON not in sym_first:
                    all_nullable = False
                    break
            else:
                # Literal or symbol not declared as nonterminal
                result.add(sym)
                all_nullable = False
                break

        if all_nullable:
            result.add(EPSILON)

        return result

    def compute_first(self) -> dict[str, set[str]]:
        """
        Computes FIRST sets for all nonterminals using fixed-point iteration.

        Iterates until no FIRST set changes, naturally resolving direct,
        indirect, and mutual left recursion.
        """
        first_sets: dict[str, set[str]] = {
            nt: set() for nt in self.grammar.nonterminals
        }

        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                lhs = prod.lhs
                if lhs not in first_sets:
                    first_sets[lhs] = set()

                before_count = len(first_sets[lhs])
                rhs_first = self.first_of_sequence(prod.rhs, first_sets)
                first_sets[lhs].update(rhs_first)

                if len(first_sets[lhs]) > before_count:
                    changed = True

        return first_sets

    def compute_follow(
        self, first_sets: dict[str, set[str]]
    ) -> dict[str, set[str]]:
        r"""
        Computes FOLLOW sets for all nonterminals using fixed-point iteration.

        Rules:
        1. Place $ in FOLLOW(start_symbol).
        2. For A -> α B β:
           - Add FIRST(β) \ {ε} to FOLLOW(B).
           - If ε ∈ FIRST(β) (or β is empty), add FOLLOW(A) to FOLLOW(B).
        3. Iterate to fixed point.
        4. Epsilon is NEVER in any FOLLOW set.
        """
        follow_sets: dict[str, set[str]] = {
            nt: set() for nt in self.grammar.nonterminals
        }

        # Rule 1: End marker in FOLLOW of start symbol
        if self.grammar.start_symbol and self.grammar.start_symbol in follow_sets:
            follow_sets[self.grammar.start_symbol].add(END_MARKER)

        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                lhs = prod.lhs
                lhs_follow = follow_sets.get(lhs, set())

                rhs = prod.rhs
                for i, sym in enumerate(rhs):
                    if sym in self.nonterminals:
                        suffix = rhs[i + 1:]
                        suffix_first = self.first_of_sequence(suffix, first_sets)

                        before_count = len(follow_sets[sym])

                        # Add FIRST(suffix) \ {ε}
                        follow_sets[sym].update(suffix_first - {EPSILON})

                        # If suffix is nullable or empty, add FOLLOW(lhs)
                        if EPSILON in suffix_first or not suffix:
                            follow_sets[sym].update(lhs_follow)

                        # Invariant: Epsilon must NEVER be in any FOLLOW set
                        follow_sets[sym].discard(EPSILON)

                        if len(follow_sets[sym]) > before_count:
                            changed = True

        return follow_sets
