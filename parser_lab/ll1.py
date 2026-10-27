"""
MiniLang-X Parser Lab — LL(1) Predictive Parsing Table & Table-Driven Parser
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from parser_lab.grammar import Grammar, Production, EPSILON, END_MARKER
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.parse_tree import ParseTreeNode


@dataclass
class LL1Conflict:
    """Represents a conflict in an LL(1) parsing table cell."""
    nonterminal: str
    terminal: str
    conflict_type: str  # "FIRST/FIRST" or "FIRST/FOLLOW"
    productions: list[Production]
    message: str

    def to_dict(self) -> dict:
        return {
            "nonterminal": self.nonterminal,
            "terminal": self.terminal,
            "conflict_type": self.conflict_type,
            "productions": [p.to_dict() for p in self.productions],
            "message": self.message,
        }


@dataclass
class LL1TableResult:
    """Container for the generated LL(1) parsing table and conflict diagnostics."""
    table: dict[str, dict[str, list[Production]]]
    is_ll1: bool
    conflicts: list[LL1Conflict]
    terminals: list[str]  # Column headers (including $)
    nonterminals: list[str]  # Row headers

    def to_dict(self) -> dict:
        serialized_table: dict[str, dict[str, list[dict]]] = {}
        for nt, row in self.table.items():
            serialized_table[nt] = {}
            for term, prods in row.items():
                serialized_table[nt][term] = [p.to_dict() for p in prods]

        return {
            "is_ll1": self.is_ll1,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "terminals": list(self.terminals),
            "nonterminals": list(self.nonterminals),
            "table": serialized_table,
        }


@dataclass
class LL1TraceStep:
    """A single step in the LL(1) stack-based parsing trace."""
    step: int
    stack: list[str]
    remaining_input: list[str]
    action: str
    production: Optional[str] = None
    status: str = "expand"  # "expand", "match", "accept", "error"

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "stack": list(self.stack),
            "remaining_input": list(self.remaining_input),
            "action": self.action,
            "production": self.production,
            "status": self.status,
        }


@dataclass
class LL1ParseResult:
    """Outcome of parsing an input sequence using an LL(1) parser."""
    accepted: bool
    is_ll1: bool
    trace: list[LL1TraceStep]
    parse_tree: Optional[ParseTreeNode] = None
    error: Optional[str] = None
    tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "is_ll1": self.is_ll1,
            "tokens": list(self.tokens),
            "trace": [s.to_dict() for s in self.trace],
            "parse_tree": self.parse_tree.to_dict() if self.parse_tree else None,
            "error": self.error,
        }


class LL1TableGenerator:
    """Constructs the predictive parsing table M[A, a] and checks for conflicts."""

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.calc = FirstFollowCalculator(grammar)
        self.first_follow = self.calc.compute()

    def generate(self) -> LL1TableResult:
        # Table columns: all terminals plus end marker $
        columns = [t for t in self.grammar.terminals if t != EPSILON and t != END_MARKER]
        columns.append(END_MARKER)

        rows = list(self.grammar.nonterminals)

        table: dict[str, dict[str, list[Production]]] = {
            nt: {term: [] for term in columns} for nt in rows
        }

        # Raw symbol FIRST sets for sequence calculation
        raw_first = self.calc.compute_first()
        raw_follow = self.calc.compute_follow(raw_first)

        # Populate table
        for prod in self.grammar.productions:
            lhs = prod.lhs
            rhs = prod.rhs

            # Compute FIRST(rhs)
            rhs_first = self.calc.first_of_sequence(rhs, raw_first)

            # Rule 1: For each terminal a in FIRST(rhs) \ {ε}, add A -> rhs to M[A, a]
            for term in rhs_first:
                if term != EPSILON and term in table.get(lhs, {}):
                    table[lhs][term].append(prod)

            # Rule 2: If ε in FIRST(rhs), add A -> rhs to M[A, b] for each b in FOLLOW(A)
            if EPSILON in rhs_first:
                for follow_term in raw_follow.get(lhs, set()):
                    if follow_term in table.get(lhs, {}):
                        # Avoid adding identical production twice if term is in both FIRST and FOLLOW
                        if prod not in table[lhs][follow_term]:
                            table[lhs][follow_term].append(prod)

        # Detect conflicts
        conflicts: list[LL1Conflict] = []
        for nt in rows:
            for term in columns:
                prods = table[nt][term]
                if len(prods) > 1:
                    # Classify conflict type
                    conflict_type = self._classify_conflict(prods, raw_first, raw_follow, nt, term)
                    msg = (
                        f"{conflict_type} conflict at M[{nt}, {term}]: "
                        f"Multiple productions {tuple(str(p) for p in prods)} compete for lookahead '{term}'."
                    )
                    conflicts.append(
                        LL1Conflict(
                            nonterminal=nt,
                            terminal=term,
                            conflict_type=conflict_type,
                            productions=prods,
                            message=msg,
                        )
                    )

        is_ll1 = len(conflicts) == 0
        return LL1TableResult(
            table=table,
            is_ll1=is_ll1,
            conflicts=conflicts,
            terminals=columns,
            nonterminals=rows,
        )

    def _classify_conflict(
        self,
        prods: list[Production],
        raw_first: dict[str, set[str]],
        raw_follow: dict[str, set[str]],
        nt: str,
        term: str,
    ) -> str:
        """Determines if a conflict is FIRST/FIRST or FIRST/FOLLOW."""
        first_count = 0
        follow_count = 0
        for p in prods:
            rf = self.calc.first_of_sequence(p.rhs, raw_first)
            if term in rf:
                first_count += 1
            elif EPSILON in rf and term in raw_follow.get(nt, set()):
                follow_count += 1

        if first_count >= 2:
            return "FIRST/FIRST"
        if first_count >= 1 and follow_count >= 1:
            return "FIRST/FOLLOW"
        return "TABLE CONFLICT"


class LL1Parser:
    """
    Executes table-driven LL(1) predictive parsing using an explicit stack
    and constructs a parse tree for accepted inputs.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.generator = LL1TableGenerator(grammar)
        self.table_result = self.generator.generate()
        self.table = self.table_result.table

    def parse(self, input_tokens: Sequence[str], max_steps: int = 5000) -> LL1ParseResult:
        tokens = list(input_tokens)
        input_buffer = tokens + [END_MARKER]
        ip = 0  # Input pointer

        if not self.grammar.start_symbol:
            return LL1ParseResult(
                accepted=False,
                is_ll1=self.table_result.is_ll1,
                trace=[],
                error="Grammar has no valid start symbol defined.",
                tokens=tokens,
            )

        root_node = ParseTreeNode(symbol=self.grammar.start_symbol)
        # Stack entries store pairs of: (grammar_symbol, parse_tree_node)
        stack: list[tuple[str, Optional[ParseTreeNode]]] = [
            (END_MARKER, None),
            (self.grammar.start_symbol, root_node),
        ]

        trace: list[LL1TraceStep] = []
        step_count = 0

        while stack:
            step_count += 1
            if step_count > max_steps:
                return LL1ParseResult(
                    accepted=False,
                    is_ll1=self.table_result.is_ll1,
                    trace=trace,
                    error=f"Maximum parsing step limit ({max_steps}) exceeded. Possible grammar loop.",
                    tokens=tokens,
                )

            current_stack_symbols = [item[0] for item in stack]
            current_remaining = input_buffer[ip:]
            top_sym, top_node = stack[-1]
            lookahead = input_buffer[ip]

            # Case 1: Stack top is end marker $
            if top_sym == END_MARKER:
                if lookahead == END_MARKER:
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action="Accept input string",
                            status="accept",
                        )
                    )
                    return LL1ParseResult(
                        accepted=True,
                        is_ll1=self.table_result.is_ll1,
                        trace=trace,
                        parse_tree=root_node,
                        tokens=tokens,
                    )
                else:
                    err = (
                        f"Terminal mismatch: stack is exhausted at '$' but input still contains "
                        f"'{lookahead}' at token position {ip + 1}."
                    )
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action=f"Error: {err}",
                            status="error",
                        )
                    )
                    return LL1ParseResult(
                        accepted=False,
                        is_ll1=self.table_result.is_ll1,
                        trace=trace,
                        error=err,
                        tokens=tokens,
                    )

            # Case 2: Stack top is terminal or $
            if top_sym not in self.grammar.nonterminals:
                if top_sym == lookahead:
                    # Match
                    if top_node is not None:
                        top_node.is_terminal = True
                    stack.pop()
                    ip += 1
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action=f"Match terminal '{top_sym}'",
                            status="match",
                        )
                    )
                else:
                    err = (
                        f"Terminal mismatch: expected '{top_sym}', but found '{lookahead}' "
                        f"at token position {ip + 1}."
                    )
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action=f"Error: {err}",
                            status="error",
                        )
                    )
                    return LL1ParseResult(
                        accepted=False,
                        is_ll1=self.table_result.is_ll1,
                        trace=trace,
                        error=err,
                        tokens=tokens,
                    )

            # Case 3: Stack top is nonterminal
            else:
                row = self.table.get(top_sym, {})
                prods = row.get(lookahead, [])

                if not prods:
                    # Check what terminals were expected in this row
                    expected = [t for t, p in row.items() if len(p) > 0]
                    expected_str = ", ".join(f"'{e}'" for e in expected) if expected else "none"
                    err = (
                        f"Syntax Error: No LL(1) table entry for M[{top_sym}, {lookahead}]. "
                        f"Expected lookahead in {{{expected_str}}} at token position {ip + 1}."
                    )
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action=f"Error: {err}",
                            status="error",
                        )
                    )
                    return LL1ParseResult(
                        accepted=False,
                        is_ll1=self.table_result.is_ll1,
                        trace=trace,
                        error=err,
                        tokens=tokens,
                    )

                if len(prods) > 1:
                    err = (
                        f"Non-LL(1) Table Conflict at M[{top_sym}, {lookahead}]: "
                        f"{len(prods)} competing productions {tuple(str(p) for p in prods)}."
                    )
                    trace.append(
                        LL1TraceStep(
                            step=step_count,
                            stack=current_stack_symbols,
                            remaining_input=current_remaining,
                            action=f"Conflict: {err}",
                            status="error",
                        )
                    )
                    return LL1ParseResult(
                        accepted=False,
                        is_ll1=self.table_result.is_ll1,
                        trace=trace,
                        error=err,
                        tokens=tokens,
                    )

                selected_prod = prods[0]
                stack.pop()

                # Expand nonterminal
                trace.append(
                    LL1TraceStep(
                        step=step_count,
                        stack=current_stack_symbols,
                        remaining_input=current_remaining,
                        action=f"Output {selected_prod}",
                        production=str(selected_prod),
                        status="expand",
                    )
                )

                # Attach parse tree children
                if selected_prod.is_epsilon:
                    if top_node is not None:
                        top_node.add_child(ParseTreeNode(symbol=EPSILON, is_terminal=True))
                else:
                    children = [
                        ParseTreeNode(symbol=s) for s in selected_prod.rhs
                    ]
                    if top_node is not None:
                        top_node.children = children

                    # Push symbols onto stack in reverse order so leftmost symbol is on top
                    for sym, child_node in reversed(list(zip(selected_prod.rhs, children))):
                        stack.append((sym, child_node))

        return LL1ParseResult(
            accepted=False,
            is_ll1=self.table_result.is_ll1,
            trace=trace,
            error="Unexpected termination of parser stack loop.",
            tokens=tokens,
        )
