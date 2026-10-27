"""
MiniLang-X Parser Lab — Common Bottom-Up LR Parsing Infrastructure
Provides AugmentedGrammar, LR(0) and LR(1) items, actions, conflict reporting,
parsing tables, and stack-driven execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence, Any

from parser_lab.grammar import Grammar, Production, EPSILON, END_MARKER
from parser_lab.parse_tree import ParseTreeNode


class AugmentedGrammar:
    """
    Augments a Context-Free Grammar with a new unique start production S' -> S (prod 0).
    Maintains a deterministic 0-indexed list of productions.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.original_grammar = grammar

        # Formulate augmented start symbol that doesn't collide
        start = grammar.start_symbol
        aug_start = f"{start}'"
        while aug_start in grammar.nonterminals or aug_start in grammar.terminals:
            aug_start += "'"
        self.augmented_start = aug_start

        # Prod 0 is always the augmented start production
        self.productions: list[Production] = [
            Production(lhs=aug_start, rhs=(start,), line=0)
        ] + list(grammar.productions)

        # Nonterminals list with augmented start at index 0
        self.nonterminals: list[str] = [aug_start] + [
            nt for nt in grammar.nonterminals if nt != aug_start
        ]
        self.terminals: list[str] = [
            t for t in grammar.terminals if t != EPSILON and t != END_MARKER
        ]

    def production_symbols(self, prod_id: int) -> tuple[str, ...]:
        """
        Returns the sequence of symbols on RHS. Epsilon productions derive
        an empty sequence of actual symbols.
        """
        prod = self.productions[prod_id]
        if prod.is_epsilon:
            return ()
        return prod.rhs

    def to_productions_dict(self) -> list[dict]:
        """Serializes productions with their IDs for frontend display."""
        result = []
        for idx, prod in enumerate(self.productions):
            rhs_str = " ".join(prod.rhs) if prod.rhs else EPSILON
            result.append({
                "id": idx,
                "lhs": prod.lhs,
                "rhs": list(prod.rhs),
                "text": f"({idx}) {prod.lhs} -> {rhs_str}",
                "is_epsilon": prod.is_epsilon,
            })
        return result


@dataclass(frozen=True, order=True)
class LR0Item:
    """Represents an LR(0) item [A -> α . β] referencing a production index."""
    prod_id: int
    dot: int

    def next_symbol(self, aug_grammar: AugmentedGrammar) -> Optional[str]:
        symbols = aug_grammar.production_symbols(self.prod_id)
        if self.dot < len(symbols):
            return symbols[self.dot]
        return None

    def is_complete(self, aug_grammar: AugmentedGrammar) -> bool:
        symbols = aug_grammar.production_symbols(self.prod_id)
        return self.dot >= len(symbols)

    def advance(self) -> LR0Item:
        return LR0Item(self.prod_id, self.dot + 1)

    def format(self, aug_grammar: AugmentedGrammar) -> str:
        prod = aug_grammar.productions[self.prod_id]
        symbols = list(aug_grammar.production_symbols(self.prod_id))
        dotted = symbols[:self.dot] + ["•"] + symbols[self.dot:]
        rhs_str = " ".join(dotted) if dotted else "•"
        return f"{prod.lhs} -> {rhs_str}"


@dataclass(frozen=True, order=True)
class LR1Item:
    """Represents an LR(1) item [A -> α . β, a] with a lookahead terminal."""
    prod_id: int
    dot: int
    lookahead: str

    @property
    def core(self) -> LR0Item:
        return LR0Item(self.prod_id, self.dot)

    def next_symbol(self, aug_grammar: AugmentedGrammar) -> Optional[str]:
        symbols = aug_grammar.production_symbols(self.prod_id)
        if self.dot < len(symbols):
            return symbols[self.dot]
        return None

    def is_complete(self, aug_grammar: AugmentedGrammar) -> bool:
        symbols = aug_grammar.production_symbols(self.prod_id)
        return self.dot >= len(symbols)

    def advance(self) -> LR1Item:
        return LR1Item(self.prod_id, self.dot + 1, self.lookahead)

    def format(self, aug_grammar: AugmentedGrammar) -> str:
        prod = aug_grammar.productions[self.prod_id]
        symbols = list(aug_grammar.production_symbols(self.prod_id))
        dotted = symbols[:self.dot] + ["•"] + symbols[self.dot:]
        rhs_str = " ".join(dotted) if dotted else "•"
        return f"[{prod.lhs} -> {rhs_str}, {self.lookahead}]"


@dataclass(frozen=True)
class LRAction:
    """Represents a shift, reduce, or accept action in an LR ACTION table."""
    action_type: str  # "shift", "reduce", "accept"
    target: int = 0  # target state for shift; production index for reduce
    production: Optional[str] = None  # Text of the production for reduce actions

    def to_str(self) -> str:
        if self.action_type == "shift":
            return f"s{self.target}"
        elif self.action_type == "reduce":
            return f"r{self.target}"
        elif self.action_type == "accept":
            return "acc"
        return ""

    def to_dict(self) -> dict:
        return {
            "type": self.action_type,
            "target": self.target,
            "display": self.to_str(),
            "production": self.production,
        }


@dataclass
class LRConflict:
    """Diagnostics for a Shift/Reduce or Reduce/Reduce conflict."""
    state_id: int
    symbol: str
    conflict_type: str  # "Shift/Reduce" or "Reduce/Reduce"
    actions: list[str]
    items: list[str]
    message: str

    def to_dict(self) -> dict:
        return {
            "state_id": self.state_id,
            "symbol": self.symbol,
            "conflict_type": self.conflict_type,
            "actions": list(self.actions),
            "items": list(self.items),
            "message": self.message,
        }


@dataclass
class LRTraceStep:
    """A single step in the bottom-up LR stack-driven parsing trace."""
    step: int
    state_stack: list[int]
    symbol_stack: list[str]
    remaining_input: list[str]
    action: str
    status: str = "shift"  # "shift", "reduce", "accept", "error"
    production: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "state_stack": list(self.state_stack),
            "symbol_stack": list(self.symbol_stack),
            "remaining_input": list(self.remaining_input),
            "action": self.action,
            "status": self.status,
            "production": self.production,
        }


@dataclass
class LRParseResult:
    """Outcome of parsing an input sequence using a bottom-up parser."""
    accepted: bool
    is_valid_table: bool
    trace: list[LRTraceStep]
    parse_tree: Optional[ParseTreeNode] = None
    error: Optional[str] = None
    tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "is_valid_table": self.is_valid_table,
            "tokens": list(self.tokens),
            "trace": [s.to_dict() for s in self.trace],
            "parse_tree": self.parse_tree.to_dict() if self.parse_tree else None,
            "error": self.error,
        }


@dataclass
class LRTableResult:
    """Container for generated LR ACTION and GOTO tables, item sets, and conflicts."""
    algorithm: str  # "SLR(1)", "CLR(1)", "LALR(1)"
    is_valid: bool  # True if no conflicts exist
    action_table: dict[int, dict[str, list[LRAction]]]
    goto_table: dict[int, dict[str, int]]
    conflicts: list[LRConflict]
    terminals: list[str]  # Column headers for ACTION ($ included)
    nonterminals: list[str]  # Column headers for GOTO (S' excluded)
    states_count: int
    productions: list[dict]
    item_sets: list[dict]
    transitions: list[dict]
    merged_states_info: Optional[list[dict]] = None

    def to_dict(self) -> dict:
        serialized_action: dict[str, dict[str, list[dict]]] = {}
        for state_id, row in self.action_table.items():
            serialized_action[str(state_id)] = {}
            for sym, acts in row.items():
                serialized_action[str(state_id)][sym] = [a.to_dict() for a in acts]

        serialized_goto: dict[str, dict[str, Optional[int]]] = {}
        for state_id, row in self.goto_table.items():
            serialized_goto[str(state_id)] = {}
            for nt, tgt in row.items():
                serialized_goto[str(state_id)][nt] = tgt

        return {
            "algorithm": self.algorithm,
            "is_valid": self.is_valid,
            "states_count": self.states_count,
            "terminals": list(self.terminals),
            "nonterminals": list(self.nonterminals),
            "productions": list(self.productions),
            "action_table": serialized_action,
            "goto_table": serialized_goto,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "item_sets": list(self.item_sets),
            "transitions": list(self.transitions),
            "merged_states_info": self.merged_states_info,
        }


class LRParserEngine:
    """
    Standard stack-driven LR parsing execution engine.
    Works identically for SLR(1), CLR(1), and LALR(1) parsing tables.
    """

    @staticmethod
    def parse(
        aug_grammar: AugmentedGrammar,
        action_table: dict[int, dict[str, list[LRAction]]],
        goto_table: dict[int, dict[str, int]],
        tokens: Sequence[str],
        is_valid_table: bool,
        max_steps: int = 5000,
    ) -> LRParseResult:
        token_list = list(tokens)
        input_buffer = token_list + [END_MARKER]
        ip = 0  # Input pointer

        state_stack: list[int] = [0]
        symbol_stack: list[str] = []
        tree_stack: list[ParseTreeNode] = []

        trace: list[LRTraceStep] = []
        step_count = 0

        while True:
            step_count += 1
            if step_count > max_steps:
                return LRParseResult(
                    accepted=False,
                    is_valid_table=is_valid_table,
                    trace=trace,
                    error=f"Maximum parsing step limit ({max_steps}) exceeded.",
                    tokens=token_list,
                )

            curr_state = state_stack[-1]
            lookahead = input_buffer[ip]

            actions = action_table.get(curr_state, {}).get(lookahead, [])

            if not actions:
                # Syntax error
                expected = [
                    sym for sym, acts in action_table.get(curr_state, {}).items()
                    if len(acts) > 0
                ]
                expected_str = ", ".join(f"'{s}'" for s in expected) if expected else "none"
                err_msg = (
                    f"Syntax error at token index {ip + 1} ('{lookahead}'): "
                    f"no valid action in State {curr_state}. Expected one of: {expected_str}."
                )
                trace.append(
                    LRTraceStep(
                        step=step_count,
                        state_stack=list(state_stack),
                        symbol_stack=list(symbol_stack),
                        remaining_input=list(input_buffer[ip:]),
                        action="Error: unexpected symbol",
                        status="error",
                    )
                )
                return LRParseResult(
                    accepted=False,
                    is_valid_table=is_valid_table,
                    trace=trace,
                    error=err_msg,
                    tokens=token_list,
                )

            if len(actions) > 1:
                # Conflict encountered during parse
                conflict_desc = " / ".join(a.to_str() for a in actions)
                err_msg = (
                    f"Ambiguous parse: unresolved conflict ({conflict_desc}) "
                    f"encountered at State {curr_state} on input symbol '{lookahead}'."
                )
                trace.append(
                    LRTraceStep(
                        step=step_count,
                        state_stack=list(state_stack),
                        symbol_stack=list(symbol_stack),
                        remaining_input=list(input_buffer[ip:]),
                        action=f"Error: conflict {conflict_desc}",
                        status="error",
                    )
                )
                return LRParseResult(
                    accepted=False,
                    is_valid_table=is_valid_table,
                    trace=trace,
                    error=err_msg,
                    tokens=token_list,
                )

            chosen_action = actions[0]

            if chosen_action.action_type == "shift":
                next_state = chosen_action.target
                trace.append(
                    LRTraceStep(
                        step=step_count,
                        state_stack=list(state_stack),
                        symbol_stack=list(symbol_stack),
                        remaining_input=list(input_buffer[ip:]),
                        action=f"Shift {chosen_action.to_str()}",
                        status="shift",
                    )
                )
                state_stack.append(next_state)
                symbol_stack.append(lookahead)
                tree_stack.append(ParseTreeNode(symbol=lookahead, is_terminal=True))
                ip += 1

            elif chosen_action.action_type == "reduce":
                prod_id = chosen_action.target
                prod = aug_grammar.productions[prod_id]
                prod_symbols = aug_grammar.production_symbols(prod_id)
                k = len(prod_symbols)

                rhs_display = " ".join(prod.rhs) if prod.rhs else EPSILON
                trace.append(
                    LRTraceStep(
                        step=step_count,
                        state_stack=list(state_stack),
                        symbol_stack=list(symbol_stack),
                        remaining_input=list(input_buffer[ip:]),
                        action=f"Reduce {chosen_action.to_str()} ({prod.lhs} -> {rhs_display})",
                        status="reduce",
                        production=f"{prod.lhs} -> {rhs_display}",
                    )
                )

                # Pop k items from state and symbol stacks
                if k > 0:
                    state_stack = state_stack[:-k]
                    symbol_stack = symbol_stack[:-k]
                    children = tree_stack[-k:]
                    tree_stack = tree_stack[:-k]
                else:
                    # Epsilon reduction derives epsilon leaf node
                    children = [ParseTreeNode(symbol=EPSILON, is_terminal=True)]

                parent_node = ParseTreeNode(
                    symbol=prod.lhs, is_terminal=False, children=children
                )
                tree_stack.append(parent_node)
                symbol_stack.append(prod.lhs)

                # GOTO transition on LHS
                top_state = state_stack[-1]
                goto_state = goto_table.get(top_state, {}).get(prod.lhs)
                if goto_state is None:
                    err_msg = (
                        f"GOTO error: No GOTO transition from State {top_state} "
                        f"on nonterminal '{prod.lhs}'."
                    )
                    return LRParseResult(
                        accepted=False,
                        is_valid_table=is_valid_table,
                        trace=trace,
                        error=err_msg,
                        tokens=token_list,
                    )
                state_stack.append(goto_state)

            elif chosen_action.action_type == "accept":
                trace.append(
                    LRTraceStep(
                        step=step_count,
                        state_stack=list(state_stack),
                        symbol_stack=list(symbol_stack),
                        remaining_input=list(input_buffer[ip:]),
                        action="Accept",
                        status="accept",
                    )
                )
                root_node = tree_stack[-1] if tree_stack else None
                return LRParseResult(
                    accepted=True,
                    is_valid_table=is_valid_table,
                    trace=trace,
                    parse_tree=root_node,
                    tokens=token_list,
                )
