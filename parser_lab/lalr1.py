"""
MiniLang-X Parser Lab — Look-Ahead LR(1) (LALR(1)) Parser, State Merging, and Table Generator
Merges canonical LR(1) states that have identical LR(0) cores, preserves and combines
lookahead sets, constructs merged transition graph, detects introduced or exposed conflicts,
and executes LALR(1) stack-driven parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from parser_lab.grammar import Grammar, END_MARKER, EPSILON
from parser_lab.lr_common import (
    AugmentedGrammar,
    LR0Item,
    LR1Item,
    LRAction,
    LRConflict,
    LRTableResult,
    LRParseResult,
    LRParserEngine,
)
from parser_lab.clr1 import CLR1TableGenerator, group_lr1_items


@dataclass
class LALRMergedStateInfo:
    """Detailed metadata on which canonical CLR(1) states were merged and why."""
    lalr_state_id: int
    merged_from_clr_states: list[int]
    core_items: list[str]
    was_merged: bool
    explanation: str

    def to_dict(self) -> dict:
        return {
            "lalr_state_id": self.lalr_state_id,
            "merged_from_clr_states": list(self.merged_from_clr_states),
            "core_items": list(self.core_items),
            "was_merged": self.was_merged,
            "explanation": self.explanation,
        }


class LALR1TableGenerator:
    """
    Constructs the LALR(1) parsing table by merging canonical LR(1) states
    having identical LR(0) cores. Accurately flags merge-induced conflicts.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.clr_generator = CLR1TableGenerator(grammar)
        self.aug_grammar = self.clr_generator.aug_grammar

    def build_merged_states(
        self,
    ) -> tuple[
        list[frozenset[LR1Item]],
        dict[tuple[int, str], int],
        list[LALRMergedStateInfo],
        dict[int, int],
    ]:
        """
        Builds canonical LR(1) states and merges those with identical LR(0) cores.
        Returns:
            lalr_states: list of merged LR(1) item sets
            lalr_transitions: merged transition graph (src_lalr, symbol) -> tgt_lalr
            merged_info: explanations of which states were merged
            clr_to_lalr: mapping from CLR state id to LALR state id
        """
        clr_states, clr_transitions = self.clr_generator.build_canonical_collection()

        # Group CLR states by LR(0) core
        core_to_clr_states: dict[frozenset[LR0Item], list[int]] = {}
        unique_cores: list[frozenset[LR0Item]] = []

        for clr_id, items in enumerate(clr_states):
            core = frozenset(item.core for item in items)
            if core not in core_to_clr_states:
                core_to_clr_states[core] = []
                unique_cores.append(core)
            core_to_clr_states[core].append(clr_id)

        # Build mapping from CLR state to LALR state
        clr_to_lalr: dict[int, int] = {}
        lalr_states: list[frozenset[LR1Item]] = []
        merged_info: list[LALRMergedStateInfo] = []

        for lalr_id, core in enumerate(unique_cores):
            clr_ids = core_to_clr_states[core]
            for clr_id in clr_ids:
                clr_to_lalr[clr_id] = lalr_id

            # Union items across all merged CLR states to combine lookaheads
            combined_items: set[LR1Item] = set()
            for clr_id in clr_ids:
                combined_items.update(clr_states[clr_id])
            lalr_states.append(frozenset(combined_items))

            was_merged = len(clr_ids) > 1
            core_formatted = [
                it.format(self.aug_grammar) for it in sorted(core)
            ]
            if was_merged:
                clr_str = ", ".join(f"I{s}" for s in clr_ids)
                explanation = (
                    f"State {lalr_id} was formed by merging canonical LR(1) states {clr_str} "
                    f"because they share the identical LR(0) core of {len(core)} items. "
                    f"Their lookahead sets have been combined."
                )
            else:
                explanation = f"State {lalr_id} corresponds to canonical LR(1) state I{clr_ids[0]}."

            merged_info.append(
                LALRMergedStateInfo(
                    lalr_state_id=lalr_id,
                    merged_from_clr_states=clr_ids,
                    core_items=core_formatted,
                    was_merged=was_merged,
                    explanation=explanation,
                )
            )

        # Construct merged transition graph
        lalr_transitions: dict[tuple[int, str], int] = {}
        for (src_clr, sym), tgt_clr in clr_transitions.items():
            src_lalr = clr_to_lalr[src_clr]
            tgt_lalr = clr_to_lalr[tgt_clr]
            lalr_transitions[(src_lalr, sym)] = tgt_lalr

        return lalr_states, lalr_transitions, merged_info, clr_to_lalr

    def generate(self) -> LRTableResult:
        """
        Builds the LALR(1) parsing table with full conflict detection.
        """
        lalr_states, lalr_transitions, merged_info, clr_to_lalr = self.build_merged_states()

        action_cols = list(self.aug_grammar.terminals)
        if END_MARKER not in action_cols:
            action_cols.append(END_MARKER)

        goto_cols = [
            nt for nt in self.aug_grammar.nonterminals if nt != self.aug_grammar.augmented_start
        ]

        action_table: dict[int, dict[str, list[LRAction]]] = {
            i: {t: [] for t in action_cols} for i in range(len(lalr_states))
        }
        goto_table: dict[int, dict[str, int]] = {
            i: {} for i in range(len(lalr_states))
        }

        # 1. Fill Shift actions and GOTO table
        for (src, sym), tgt in lalr_transitions.items():
            if sym in self.aug_grammar.terminals:
                action_table[src][sym].append(LRAction(action_type="shift", target=tgt))
            elif sym in goto_cols:
                goto_table[src][sym] = tgt

        # 2. Fill Reduce and Accept actions using combined LR(1) lookaheads
        for i, item_set in enumerate(lalr_states):
            for item in item_set:
                if item.is_complete(self.aug_grammar):
                    if item.prod_id == 0:
                        # [S' -> S ., $] => accept
                        if item.lookahead == END_MARKER:
                            act = LRAction(action_type="accept", target=0)
                            if act not in action_table[i][END_MARKER]:
                                action_table[i][END_MARKER].append(act)
                    else:
                        prod = self.aug_grammar.productions[item.prod_id]
                        rhs_str = " ".join(prod.rhs) if prod.rhs else EPSILON
                        prod_text = f"{prod.lhs} -> {rhs_str}"
                        lookahead = item.lookahead
                        if lookahead in action_table[i]:
                            act = LRAction(
                                action_type="reduce",
                                target=item.prod_id,
                                production=prod_text,
                            )
                            if act not in action_table[i][lookahead]:
                                action_table[i][lookahead].append(act)

        # 3. Detect conflicts and diagnose merge-induced conflicts
        conflicts: list[LRConflict] = []
        for i in range(len(lalr_states)):
            info = merged_info[i]
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

                    items_formatted = group_lr1_items(lalr_states[i], self.aug_grammar)
                    actions_formatted = [a.to_str() for a in cell_actions]

                    merge_note = ""
                    if info.was_merged and ctype == "Reduce/Reduce":
                        merge_note = (
                            f" (This Reduce/Reduce conflict was introduced by merging "
                            f"canonical LR(1) states {info.merged_from_clr_states}.)"
                        )

                    msg = (
                        f"{ctype} conflict at LALR State {i} on lookahead '{sym}': "
                        f"actions {actions_formatted} conflict.{merge_note}"
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

        is_lalr1 = len(conflicts) == 0

        # Format item sets for frontend display
        item_sets_data = []
        for i, item_set in enumerate(lalr_states):
            state_trans = {
                sym: tgt for (src, sym), tgt in lalr_transitions.items() if src == i
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
                "merged_info": merged_info[i].to_dict(),
            })

        transitions_data = [
            {"from": src, "to": tgt, "symbol": sym}
            for (src, sym), tgt in lalr_transitions.items()
        ]

        return LRTableResult(
            algorithm="LALR(1)",
            is_valid=is_lalr1,
            action_table=action_table,
            goto_table=goto_table,
            conflicts=conflicts,
            terminals=action_cols,
            nonterminals=goto_cols,
            states_count=len(lalr_states),
            productions=self.aug_grammar.to_productions_dict(),
            item_sets=item_sets_data,
            transitions=transitions_data,
            merged_states_info=[info.to_dict() for info in merged_info],
        )


class LALR1Parser:
    """
    LALR(1) table-driven parser executing on input token sequences.
    """

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.generator = LALR1TableGenerator(grammar)
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
