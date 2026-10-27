"""
MiniLang-X Parser Lab — Canonical LR(1) (CLR(1)) Parser, Item Sets, and Table Generator
Constructs LR(1) items with lookaheads, implements LR(1) CLOSURE and GOTO,
builds canonical LR(1) states, detects Shift/Reduce and Reduce/Reduce conflicts,
and executes CLR(1) stack-driven parsing.
"""

from __future__ import annotations

from typing import Optional, Sequence

from parser_lab.grammar import Grammar, END_MARKER, EPSILON
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.lr_common import (
    AugmentedGrammar,
    LR1Item,
    LRAction,
    LRConflict,
    LRTableResult,
    LRParseResult,
    LRParserEngine,
)


def lr1_closure(
    items: set[LR1Item],
    aug_grammar: AugmentedGrammar,
    raw_first: dict[str, set[str]],
    calc: FirstFollowCalculator,
) -> frozenset[LR1Item]:
    """
    Computes the LR(1) closure of a set of items:
    If [A -> α . B β, a] is in the closure:
      for each production B -> γ:
        for each b in FIRST(β a):
          add [B -> . γ, b] to the closure.
    """
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        new_items = set()
        for item in closure_set:
            sym = item.next_symbol(aug_grammar)
            if sym and sym in aug_grammar.nonterminals:
                prod_symbols = aug_grammar.production_symbols(item.prod_id)
                suffix = prod_symbols[item.dot + 1:]
                # Compute FIRST(β a)
                sequence = list(suffix) + [item.lookahead]
                lookahead_set = calc.first_of_sequence(sequence, raw_first) - {EPSILON}

                for pid, prod in enumerate(aug_grammar.productions):
                    if prod.lhs == sym:
                        for b in lookahead_set:
                            new_item = LR1Item(pid, 0, b)
                            if new_item not in closure_set and new_item not in new_items:
                                new_items.add(new_item)
                                changed = True
        closure_set.update(new_items)
    return frozenset(closure_set)


def lr1_goto(
    items: frozenset[LR1Item],
    symbol: str,
    aug_grammar: AugmentedGrammar,
    raw_first: dict[str, set[str]],
    calc: FirstFollowCalculator,
) -> frozenset[LR1Item]:
    """
    Computes LR(1) GOTO(I, X) = CLOSURE({ [A -> α X . β, a] | [A -> α . X β, a] in I }).
    """
    advanced = set()
    for item in items:
        if item.next_symbol(aug_grammar) == symbol:
            advanced.add(item.advance())
    if not advanced:
        return frozenset()
    return lr1_closure(advanced, aug_grammar, raw_first, calc)


def group_lr1_items(items: frozenset[LR1Item], aug_grammar: AugmentedGrammar) -> list[str]:
    """
    Groups LR(1) items by core for clean human-readable display:
    [A -> α . β, a / b / c]
    """
    core_map: dict[tuple[int, int], list[str]] = {}
    for item in items:
        key = (item.prod_id, item.dot)
        if key not in core_map:
            core_map[key] = []
        core_map[key].append(item.lookahead)

    result = []
    # Sort cores by production id and dot
    for (pid, dot) in sorted(core_map.keys()):
        lookaheads = sorted(core_map[(pid, dot)], key=lambda x: (x == END_MARKER, x))
        prod = aug_grammar.productions[pid]
        symbols = list(aug_grammar.production_symbols(pid))
        dotted = symbols[:dot] + ["•"] + symbols[dot:]
        rhs_str = " ".join(dotted) if dotted else "•"
        lh_str = " / ".join(lookaheads)
        result.append(f"[{prod.lhs} -> {rhs_str}, {lh_str}]")
    return result


class CLR1TableGenerator:
    """
    Constructs the canonical collection of LR(1) item sets, and generates
    the CLR(1) ACTION and GOTO tables with lookahead-based conflict detection.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.aug_grammar = AugmentedGrammar(grammar)
        self.calc = FirstFollowCalculator(grammar)
        self.raw_first = self.calc.compute_first()

    def build_canonical_collection(
        self,
    ) -> tuple[list[frozenset[LR1Item]], dict[tuple[int, str], int]]:
        """
        Constructs the canonical LR(1) item sets C = (I_0, I_1, ...).
        Returns (states, transitions).
        """
        initial_item = LR1Item(0, 0, END_MARKER)
        I0 = lr1_closure({initial_item}, self.aug_grammar, self.raw_first, self.calc)

        states: list[frozenset[LR1Item]] = [I0]
        state_map: dict[frozenset[LR1Item], int] = {I0: 0}
        transitions: dict[tuple[int, str], int] = {}

        symbols_order = [
            nt for nt in self.aug_grammar.nonterminals if nt != self.aug_grammar.augmented_start
        ] + [t for t in self.aug_grammar.terminals if t != END_MARKER]

        queue: list[int] = [0]
        while queue:
            curr_id = queue.pop(0)
            curr_items = states[curr_id]

            active_symbols = set()
            for item in curr_items:
                ns = item.next_symbol(self.aug_grammar)
                if ns:
                    active_symbols.add(ns)

            ordered_active = [s for s in symbols_order if s in active_symbols] + sorted(
                [s for s in active_symbols if s not in symbols_order]
            )

            for sym in ordered_active:
                next_items = lr1_goto(curr_items, sym, self.aug_grammar, self.raw_first, self.calc)
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
        Builds the CLR(1) parsing table with full conflict detection.
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

        # 1. Fill Shift actions and GOTO table
        for (src, sym), tgt in transitions.items():
            if sym in self.aug_grammar.terminals:
                action_table[src][sym].append(LRAction(action_type="shift", target=tgt))
            elif sym in goto_cols:
                goto_table[src][sym] = tgt

        # 2. Fill Reduce and Accept actions using LR(1) lookahead
        for i, item_set in enumerate(states):
            for item in item_set:
                if item.is_complete(self.aug_grammar):
                    if item.prod_id == 0:
                        # [S' -> S ., $] => accept
                        if item.lookahead == END_MARKER:
                            action_table[i][END_MARKER].append(
                                LRAction(action_type="accept", target=0)
                            )
                    else:
                        prod = self.aug_grammar.productions[item.prod_id]
                        rhs_str = " ".join(prod.rhs) if prod.rhs else EPSILON
                        prod_text = f"{prod.lhs} -> {rhs_str}"
                        # In CLR(1), reduce ONLY on item's lookahead symbol
                        lookahead = item.lookahead
                        if lookahead in action_table[i]:
                            act = LRAction(
                                action_type="reduce",
                                target=item.prod_id,
                                production=prod_text,
                            )
                            if act not in action_table[i][lookahead]:
                                action_table[i][lookahead].append(act)

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

                    items_formatted = group_lr1_items(states[i], self.aug_grammar)
                    actions_formatted = [a.to_str() for a in cell_actions]
                    msg = (
                        f"{ctype} conflict at State {i} on lookahead '{sym}': "
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

        is_clr1 = len(conflicts) == 0

        # Format item sets for frontend display
        item_sets_data = []
        for i, item_set in enumerate(states):
            state_trans = {
                sym: tgt for (src, sym), tgt in transitions.items() if src == i
            }
            item_sets_data.append({
                "state_id": i,
                "items": group_lr1_items(item_set, self.aug_grammar),
                "raw_items": [
                    {
                        "prod_id": it.prod_id,
                        "dot": it.dot,
                        "lookahead": it.lookahead,
                        "text": it.format(self.aug_grammar),
                    }
                    for it in sorted(item_set)
                ],
                "transitions": state_trans,
            })

        transitions_data = [
            {"from": src, "to": tgt, "symbol": sym}
            for (src, sym), tgt in transitions.items()
        ]

        return LRTableResult(
            algorithm="CLR(1)",
            is_valid=is_clr1,
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


class CLR1Parser:
    """
    Canonical LR(1) table-driven parser executing on input token sequences.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.generator = CLR1TableGenerator(grammar)
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
