"""
Unit tests for LALR(1) parsing:
Core extraction, canonical LR(1) state merging, combined lookahead propagation,
merged transition graph, Reduce/Reduce conflict detection on classic grammar,
parsing expression grammar, and parse tree construction.
"""

import unittest

from parser_lab.grammar import parse_grammar_text
from parser_lab.lalr1 import LALR1TableGenerator, LALR1Parser
from parser_lab.clr1 import CLR1TableGenerator
from parser_lab.slr1 import SLR1TableGenerator
from parser_lab.tokenizer import tokenize_input_string


class LALR1ParsingTests(unittest.TestCase):
    def setUp(self):
        # Left-recursive expression grammar
        self.expr_grammar_text = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
        """
        self.grammar, _ = parse_grammar_text(self.expr_grammar_text)
        self.assertIsNotNone(self.grammar)

        # Classic LR(1)-but-not-LALR(1) grammar
        self.classic_grammar_text = """
        S -> a A d | b A e | a B e | b B d
        A -> c
        B -> c
        """
        self.classic_grammar, _ = parse_grammar_text(self.classic_grammar_text)
        self.assertIsNotNone(self.classic_grammar)

    def test_classic_grammar_introduces_reduce_reduce_conflict_in_lalr1(self):
        # 1. Verify CLR(1) has zero conflicts
        clr_gen = CLR1TableGenerator(self.classic_grammar)
        clr_res = clr_gen.generate()
        self.assertTrue(clr_res.is_valid)
        self.assertEqual(len(clr_res.conflicts), 0)

        # 2. Verify LALR(1) merges states and detects Reduce/Reduce conflict
        lalr_gen = LALR1TableGenerator(self.classic_grammar)
        lalr_res = lalr_gen.generate()

        self.assertFalse(lalr_res.is_valid, "LALR(1) should fail with Reduce/Reduce conflicts.")
        self.assertGreater(len(lalr_res.conflicts), 0)

        rr_conflicts = [c for c in lalr_res.conflicts if c.conflict_type == "Reduce/Reduce"]
        self.assertGreater(len(rr_conflicts), 0)

        # The conflicts occur on 'd' and 'e'
        conflict_symbols = {c.symbol for c in rr_conflicts}
        self.assertTrue("d" in conflict_symbols or "e" in conflict_symbols)

        # Verify merged state metadata
        merged_states = [m for m in lalr_res.merged_states_info if m["was_merged"]]
        self.assertGreater(len(merged_states), 0)
        for m in merged_states:
            self.assertIn("because they share the identical LR(0) core", m["explanation"])

    def test_lalr1_expression_grammar_states_match_lr0_count(self):
        # Expression grammar: LR(0) / SLR(1) has 12 states.
        # LALR(1) merges CLR(1) states to exactly the same number of states as LR(0): 12!
        slr_gen = SLR1TableGenerator(self.grammar)
        slr_res = slr_gen.generate()

        lalr_gen = LALR1TableGenerator(self.grammar)
        lalr_res = lalr_gen.generate()

        self.assertEqual(lalr_res.states_count, slr_res.states_count)
        self.assertEqual(lalr_res.states_count, 12)
        self.assertTrue(lalr_res.is_valid)
        self.assertEqual(len(lalr_res.conflicts), 0)

    def test_lalr1_parse_valid_inputs(self):
        parser = LALR1Parser(self.grammar)

        valid_inputs = [
            "id",
            "id + id",
            "id * id + id",
            "( id + id ) * id",
        ]
        for inp in valid_inputs:
            tokens, _ = tokenize_input_string(inp, self.grammar.terminals)
            res = parser.parse(tokens)
            self.assertTrue(res.accepted, f"Failed on '{inp}': {res.error}")
            self.assertIsNotNone(res.parse_tree)
            self.assertEqual(res.parse_tree.symbol, "E")

    def test_lalr1_parse_invalid_inputs(self):
        parser = LALR1Parser(self.grammar)

        invalid_inputs = [
            "id +",
            "( id + id",
            "id *",
        ]
        for inp in invalid_inputs:
            tokens, _ = tokenize_input_string(inp, self.grammar.terminals)
            res = parser.parse(tokens)
            self.assertFalse(res.accepted)
            self.assertIsNotNone(res.error)


if __name__ == "__main__":
    unittest.main()
