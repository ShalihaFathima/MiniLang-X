"""
MiniLang-X Parser Lab — Recursive Descent Parser with Left Recursion Detection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from parser_lab.grammar import Grammar, Production, EPSILON, END_MARKER
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.parse_tree import ParseTreeNode


@dataclass
class LeftRecursionReport:
    """Contains diagnostics on direct and indirect left recursion in grammar."""
    has_left_recursion: bool
    direct_left_recursion: list[str]  # Nonterminals with direct left recursion
    indirect_left_recursion: list[list[str]]  # Cycles of indirect left recursion
    explanation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "has_left_recursion": self.has_left_recursion,
            "direct_left_recursion": list(self.direct_left_recursion),
            "indirect_left_recursion": [list(cycle) for cycle in self.indirect_left_recursion],
            "explanation": self.explanation,
        }


@dataclass
class RDTraceStep:
    """A single step in a recursive descent parser trace."""
    step: int
    depth: int
    action: str
    lookahead: str
    status: str = "enter"  # "enter", "try", "match", "backtrack", "success", "error"

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "depth": self.depth,
            "action": self.action,
            "lookahead": self.lookahead,
            "status": self.status,
        }


@dataclass
class RDParseResult:
    """Outcome of parsing using Recursive Descent."""
    accepted: bool
    has_left_recursion: bool
    trace: list[RDTraceStep]
    parse_tree: Optional[ParseTreeNode] = None
    error: Optional[str] = None
    tokens: list[str] = field(default_factory=list)
    left_recursion: Optional[LeftRecursionReport] = None

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "has_left_recursion": self.has_left_recursion,
            "tokens": list(self.tokens),
            "trace": [s.to_dict() for s in self.trace],
            "parse_tree": self.parse_tree.to_dict() if self.parse_tree else None,
            "error": self.error,
            "left_recursion": self.left_recursion.to_dict() if self.left_recursion else None,
        }


class LeftRecursionDetector:
    """Analyzes a grammar to detect direct and indirect left recursion."""

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.calc = FirstFollowCalculator(grammar)
        self.first_sets = self.calc.compute_first()

    def analyze(self) -> LeftRecursionReport:
        direct: list[str] = []
        nt_set = set(self.grammar.nonterminals)

        # 1. Detect direct left recursion: A -> A α
        for prod in self.grammar.productions:
            if prod.rhs and prod.rhs[0] == prod.lhs:
                if prod.lhs not in direct:
                    direct.append(prod.lhs)

        # 2. Build leading nonterminal dependency graph for indirect left recursion
        # Edge A -> B exists if A -> α B ... where α derives ε (or α is empty)
        leading_graph: dict[str, set[str]] = {nt: set() for nt in self.grammar.nonterminals}
        for prod in self.grammar.productions:
            lhs = prod.lhs
            for sym in prod.rhs:
                if sym == EPSILON:
                    continue
                if sym in nt_set:
                    leading_graph[lhs].add(sym)
                    # If sym can derive epsilon, continue to next symbol
                    if EPSILON not in self.first_sets.get(sym, set()):
                        break
                else:
                    # Terminal stops leading derivation
                    break

        # Detect cycles in leading graph using DFS
        indirect_cycles: list[list[str]] = []

        def find_cycles(start_node: str):
            visited: list[str] = []

            def dfs(curr: str):
                visited.append(curr)
                for neighbor in leading_graph.get(curr, set()):
                    if neighbor == start_node and len(visited) > 1:
                        cycle = list(visited) + [start_node]
                        # Avoid duplicates
                        if cycle not in indirect_cycles and not any(
                            set(cycle) == set(c) for c in indirect_cycles
                        ):
                            indirect_cycles.append(cycle)
                    elif neighbor not in visited:
                        dfs(neighbor)
                visited.pop()

            dfs(start_node)

        for nt in self.grammar.nonterminals:
            find_cycles(nt)

        has_lr = bool(direct or indirect_cycles)
        explanation = None
        if has_lr:
            parts = []
            if direct:
                parts.append(
                    f"Direct left recursion in nonterminals: {', '.join(direct)}."
                )
            if indirect_cycles:
                cycles_str = "; ".join(" -> ".join(c) for c in indirect_cycles)
                parts.append(f"Indirect left recursion cycles: {cycles_str}.")
            parts.append(
                "Conventional predictive top-down recursive descent cannot directly parse "
                "left-recursive grammars because calling the leading nonterminal immediately "
                "leads to infinite recursion."
            )
            explanation = " ".join(parts)

        return LeftRecursionReport(
            has_left_recursion=has_lr,
            direct_left_recursion=direct,
            indirect_left_recursion=indirect_cycles,
            explanation=explanation,
        )


class RecursiveDescentParser:
    """
    Simulates a predictive recursive descent parser with backtracking support
    and safeguards against infinite recursion.
    """

    def __init__(
        self,
        grammar: Grammar,
        max_depth: int = 70,
        max_steps: int = 3000,
    ) -> None:
        self.grammar = grammar
        self.max_depth = max_depth
        self.max_steps = max_steps
        self.detector = LeftRecursionDetector(grammar)
        self.left_recursion = self.detector.analyze()
        self.calc = FirstFollowCalculator(grammar)
        self.first_sets = self.calc.compute_first()
        self.follow_sets = self.calc.compute_follow(self.first_sets)

    def parse(self, input_tokens: Sequence[str]) -> RDParseResult:
        tokens = list(input_tokens)
        input_buffer = tokens + [END_MARKER]
        ip = 0
        step_counter = [0]
        trace: list[RDTraceStep] = []
        recursion_error: list[str] = []

        if not self.grammar.start_symbol:
            return RDParseResult(
                accepted=False,
                has_left_recursion=self.left_recursion.has_left_recursion,
                trace=[],
                error="Grammar has no valid start symbol defined.",
                tokens=tokens,
                left_recursion=self.left_recursion,
            )

        def record(depth: int, action: str, status: str = "enter"):
            step_counter[0] += 1
            curr_lookahead = input_buffer[ip] if ip < len(input_buffer) else END_MARKER
            trace.append(
                RDTraceStep(
                    step=step_counter[0],
                    depth=depth,
                    action=action,
                    lookahead=curr_lookahead,
                    status=status,
                )
            )

        def parse_symbol(nt: str, depth: int) -> Optional[ParseTreeNode]:
            nonlocal ip
            if depth > self.max_depth:
                if not recursion_error:
                    msg = (
                        f"Maximum recursion depth ({self.max_depth}) exceeded in parse_{nt}(). "
                        f"Left recursion or cyclical grammar expansion detected."
                    )
                    recursion_error.append(msg)
                    record(depth, f"Recursion Limit Error: {msg}", status="error")
                return None

            if step_counter[0] >= self.max_steps:
                if not recursion_error:
                    msg = f"Maximum step execution limit ({self.max_steps}) exceeded."
                    recursion_error.append(msg)
                    record(depth, f"Step Limit Error: {msg}", status="error")
                return None

            record(depth, f"Enter parse_{nt}()", status="enter")
            current_lookahead = input_buffer[ip]

            # Get candidate productions for nt
            candidates = self.grammar.productions_for(nt)
            if not candidates:
                record(depth, f"Error: No production rules defined for '{nt}'", status="error")
                return None

            # Sort candidate productions so predictive matches (lookahead in FIRST) are tried first
            def candidate_priority(p: Production) -> int:
                rf = self.calc.first_of_sequence(p.rhs, self.first_sets)
                if current_lookahead in rf:
                    return 0  # Highest priority: direct FIRST match
                if EPSILON in rf and current_lookahead in self.follow_sets.get(nt, set()):
                    return 1  # Next priority: nullable with lookahead in FOLLOW
                return 2

            ordered_candidates = sorted(candidates, key=candidate_priority)

            for prod in ordered_candidates:
                record(depth, f"Try {prod}", status="try")
                saved_ip = ip
                matched_children: list[ParseTreeNode] = []
                alternative_success = True

                if prod.is_epsilon:
                    # Epsilon production: consume nothing
                    matched_children.append(
                        ParseTreeNode(symbol=EPSILON, is_terminal=True)
                    )
                else:
                    for sym in prod.rhs:
                        if recursion_error:
                            alternative_success = False
                            break

                        if sym in self.grammar.nonterminals:
                            # Recursive call for nonterminal
                            child_node = parse_symbol(sym, depth + 1)
                            if child_node is not None:
                                matched_children.append(child_node)
                            else:
                                alternative_success = False
                                break
                        else:
                            # Terminal match
                            look = input_buffer[ip]
                            if sym == look:
                                record(depth, f"Match terminal '{sym}'", status="match")
                                matched_children.append(
                                    ParseTreeNode(symbol=sym, is_terminal=True)
                                )
                                ip += 1
                            else:
                                record(
                                    depth,
                                    f"Terminal mismatch: expected '{sym}', found '{look}'",
                                    status="error",
                                )
                                alternative_success = False
                                break

                if alternative_success and not recursion_error:
                    node = ParseTreeNode(symbol=nt, children=matched_children)
                    record(depth, f"Exit parse_{nt}() [Success: {prod}]", status="success")
                    return node
                else:
                    # Backtrack
                    if ip != saved_ip:
                        record(
                            depth,
                            f"Backtrack from {prod}: restoring input pointer from {ip} to {saved_ip}",
                            status="backtrack",
                        )
                    ip = saved_ip

                if recursion_error:
                    return None

            record(depth, f"Exit parse_{nt}() [Failed to match any alternative]", status="error")
            return None

        # Execute parse starting at start_symbol
        root = parse_symbol(self.grammar.start_symbol, depth=0)

        if recursion_error:
            return RDParseResult(
                accepted=False,
                has_left_recursion=self.left_recursion.has_left_recursion,
                trace=trace,
                error=recursion_error[0],
                tokens=tokens,
                left_recursion=self.left_recursion,
            )

        if root is not None:
            # Check if all tokens were consumed up to $
            if ip == len(tokens):
                record(0, "Accept: input string successfully parsed", status="success")
                return RDParseResult(
                    accepted=True,
                    has_left_recursion=self.left_recursion.has_left_recursion,
                    trace=trace,
                    parse_tree=root,
                    tokens=tokens,
                    left_recursion=self.left_recursion,
                )
            else:
                err = (
                    f"Syntax Error: Unconsumed input tokens remain starting at position "
                    f"{ip + 1}: '{' '.join(input_buffer[ip:])}'."
                )
                record(0, err, status="error")
                return RDParseResult(
                    accepted=False,
                    has_left_recursion=self.left_recursion.has_left_recursion,
                    trace=trace,
                    error=err,
                    tokens=tokens,
                    left_recursion=self.left_recursion,
                )

        err = (
            f"Syntax Error: Input string rejected. Could not derive input from "
            f"start symbol '{self.grammar.start_symbol}'."
        )
        return RDParseResult(
            accepted=False,
            has_left_recursion=self.left_recursion.has_left_recursion,
            trace=trace,
            error=err,
            tokens=tokens,
            left_recursion=self.left_recursion,
        )
