"""
MiniLang-X Parser Lab — SLR(1) Parser, Item Sets, and Parsing Table Generator
Augments grammar, constructs LR(0) canonical collection, builds SLR(1) ACTION/GOTO tables
using FOLLOW sets, detects Shift/Reduce and Reduce/Reduce conflicts, and executes SLR(1) parsing.
"""

from __future__ import annotations

from typing import Optional, Sequence

from parser_lab.grammar import Grammar, END_MARKER, EPSILON
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.lr_common import (
    AugmentedGrammar,
    LR0Item,
    LRAction,
    LRConflict,
    LRTableResult,
    LRParseResult,
    LRParserEngine,
)


def lr0_closure(items: set[LR0Item], aug_grammar: AugmentedGrammar) -> frozenset[LR0Item]:
    """
    Computes the LR(0) closure of a set of items.
    If [A -> α . B β] is in the closure, add [B -> . γ] for all B productions.
    """
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for item in closure_set:
            sym = item.next_symbol(aug_grammar)
            if sym and sym in aug_grammar.nonterminals:
                for pid, prod in enumerate(aug_grammar.productions):
                    if prod.lhs == sym:
                        new_item = LR0Item(pid, 0)
                        if new_item not in closure_set and new_item not in new_items:
                            new_items.add(new_item)
                            changed = True
        closure_set.update(new_items)
    return frozenset(closure_set)


def lr0_goto(items: frozenset[LR0Item], symbol: str, aug_grammar: AugmentedGrammar) -> frozenset[LR0Item]:
    """
    Computes LR(0) GOTO(I, X) = CLOSURE({ [A -> α X . β] | [A -> α . X β] in I }).
    """
    advanced = set()
    for item in items:
        if item.next_symbol(aug_grammar) == symbol:
            advanced.add(item.advance())
    if not advanced:
        return frozenset()
    return lr0_closure(advanced, aug_grammar)


class SLR1TableGenerator:
    """
    Generates canonical LR(0) item sets and constructs the SLR(1) ACTION and GOTO tables
    using nonterminal FOLLOW sets. Detects shift/reduce and reduce/reduce conflicts.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.aug_grammar = AugmentedGrammar(grammar)
        self.calc = FirstFollowCalculator(grammar)
        self.first_follow = self.calc.compute()

    def build_canonical_collection(
        self,
    ) -> tuple[list[frozenset[LR0Item]], dict[tuple[int, str], int]]:
        """
        Constructs the canonical collection of LR(0) item sets C = (I_0, I_1, ...).
        Returns (states, transitions).
        """
        initial_item = LR0Item(0, 0)
        I0 = lr0_closure({initial_item}, self.aug_grammar)

        states: list[frozenset[LR0Item]] = [I0]
        state_map: dict[frozenset[LR0Item], int] = {I0: 0}
        transitions: dict[tuple[int, str], int] = {}

        symbols_order = [
            nt for nt in self.aug_grammar.nonterminals if nt != self.aug_grammar.augmented_start
        ] + [t for t in self.aug_grammar.terminals if t != END_MARKER]

        queue: list[int] = [0]
        while queue:
            curr_id = queue.pop(0)
            curr_items = states[curr_id]

            # Find all symbols immediately following dot in this state
            active_symbols = set()
            for item in curr_items:
                ns = item.next_symbol(self.aug_grammar)
                if ns:
                    active_symbols.add(ns)

            # Process symbols in deterministic order
            ordered_active = [s for s in symbols_order if s in active_symbols] + sorted(
                [s for s in active_symbols if s not in symbols_order]
            )

            for sym in ordered_active:
                next_items = lr0_goto(curr_items, sym, self.aug_grammar)
                if not next_items:
                    continue

                if next_items not in state_map:
                    new_id = len(states)
                    states.append(next_items)
                    state_map[next_items] = new_id
                    queue.append(new_id)

                transitions[(curr_id, sym)] = state_map[next_items]

        return states, transitions

    def generate(self) -> LRTableResult:
        """
        Builds the SLR(1) parsing table with full conflict detection.
        """
        states, transitions = self.build_canonical_collection()

        action_cols = list(self.aug_grammar.terminals)
        if END_MARKER not in action_cols:
            action_cols.append(END_MARKER)

        goto_cols = [
            nt for nt in self.aug_grammar.nonterminals if nt != self.aug_grammar.augmented_start
        ]

        action_table: dict[int, dict[str, list[LRAction]]] = {
            i: {t: [] for t in action_cols} for i in range(len(states))
        }
        goto_table: dict[int, dict[str, int]] = {
            i: {} for i in range(len(states))
        }

        # 1. Fill Shift actions and GOTO table from state transitions
        for (src, sym), tgt in transitions.items():
            if sym in self.aug_grammar.terminals:
                action_table[src][sym].append(LRAction(action_type="shift", target=tgt))
            elif sym in goto_cols:
                goto_table[src][sym] = tgt

        # 2. Fill Reduce and Accept actions
        for i, item_set in enumerate(states):
            for item in item_set:
                if item.is_complete(self.aug_grammar):
                    if item.prod_id == 0:
                        # [S' -> S .] => accept on $
                        action_table[i][END_MARKER].append(
                            LRAction(action_type="accept", target=0)
                        )
                    else:
                        prod = self.aug_grammar.productions[item.prod_id]
                        rhs_str = " ".join(prod.rhs) if prod.rhs else EPSILON
                        prod_text = f"{prod.lhs} -> {rhs_str}"
                        # In SLR(1), reduce on all terminals in FOLLOW(prod.lhs)
                        follow_set = self.first_follow.follow.get(prod.lhs, [])
                        for a in follow_set:
                            if a in action_table[i]:
                                act = LRAction(
                                    action_type="reduce",
                                    target=item.prod_id,
                                    production=prod_text,
                                )
                                if act not in action_table[i][a]:
                                    action_table[i][a].append(act)

        # 3. Detect conflicts
        conflicts: list[LRConflict] = []
        for i in range(len(states)):
            for sym in action_cols:
                cell_actions = action_table[i][sym]
                if len(cell_actions) > 1:
                    has_shift = any(a.action_type == "shift" for a in cell_actions)
                    has_reduce = any(a.action_type == "reduce" for a in cell_actions)
                    reduce_count = sum(1 for a in cell_actions if a.action_type == "reduce")

                    if has_shift and has_reduce:
                        ctype = "Shift/Reduce"
                    elif reduce_count >= 2:
                        ctype = "Reduce/Reduce"
                    else:
                        ctype = "Action Conflict"

                    items_formatted = [
                        it.format(self.aug_grammar) for it in sorted(states[i])
                    ]
                    actions_formatted = [a.to_str() for a in cell_actions]
                    msg = (
                        f"{ctype} conflict at State {i} on terminal '{sym}': "
                        f"actions {actions_formatted} conflict."
                    )
                    conflicts.append(
                        LRConflict(
                            state_id=i,
                            symbol=sym,
                            conflict_type=ctype,
                            actions=actions_formatted,
                            items=items_formatted,
                            message=msg,
                        )
                    )

        is_slr1 = len(conflicts) == 0

        # Format item sets for frontend display
        item_sets_data = []
        for i, item_set in enumerate(states):
            state_trans = {
                sym: tgt for (src, sym), tgt in transitions.items() if src == i
            }
            item_sets_data.append({
                "state_id": i,
                "items": [it.format(self.aug_grammar) for it in sorted(item_set)],
                "raw_items": [
                    {"prod_id": it.prod_id, "dot": it.dot, "text": it.format(self.aug_grammar)}
                    for it in sorted(item_set)
                ],
                "transitions": state_trans,
            })

        transitions_data = [
            {"from": src, "to": tgt, "symbol": sym}
            for (src, sym), tgt in transitions.items()
        ]

        return LRTableResult(
            algorithm="SLR(1)",
            is_valid=is_slr1,
            action_table=action_table,
            goto_table=goto_table,
            conflicts=conflicts,
            terminals=action_cols,
            nonterminals=goto_cols,
            states_count=len(states),
            productions=self.aug_grammar.to_productions_dict(),
            item_sets=item_sets_data,
            transitions=transitions_data,
        )


class SLR1Parser:
    """
    SLR(1) table-driven parser executing on input token sequences.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.generator = SLR1TableGenerator(grammar)
        self.table_result = self.generator.generate()

    def parse(self, tokens: Sequence[str], max_steps: int = 5000) -> LRParseResult:
        return LRParserEngine.parse(
            aug_grammar=self.generator.aug_grammar,
            action_table=self.table_result.action_table,
            goto_table=self.table_result.goto_table,
            tokens=tokens,
            is_valid_table=self.table_result.is_valid,
            max_steps=max_steps,
        )
