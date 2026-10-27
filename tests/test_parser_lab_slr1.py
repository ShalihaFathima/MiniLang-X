"""
Unit tests for SLR(1) parsing: LR(0) closure, GOTO, canonical collection,
ACTION/GOTO table generation, conflict detection, parse traces, and parse trees.
"""

import unittest

from parser_lab.grammar import parse_grammar_text, EPSILON
from parser_lab.lr_common import LR0Item, AugmentedGrammar
from parser_lab.slr1 import lr0_closure, lr0_goto, SLR1TableGenerator, SLR1Parser
from parser_lab.tokenizer import tokenize_input_string


class SLR1ParsingTests(unittest.TestCase):
    def setUp(self):
        # Classic left-recursive expression grammar
        self.expr_grammar_text = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
        """
        self.grammar, _ = parse_grammar_text(self.expr_grammar_text)
        self.assertIsNotNone(self.grammar)

    def test_augmented_grammar(self):
        aug = AugmentedGrammar(self.grammar)
        self.assertEqual(aug.augmented_start, "E'")
        self.assertEqual(aug.productions[0].lhs, "E'")
        self.assertEqual(aug.productions[0].rhs, ("E",))
        self.assertEqual(len(aug.productions), 7)

    def test_lr0_closure_initial_state(self):
        aug = AugmentedGrammar(self.grammar)
        I0 = lr0_closure({LR0Item(0, 0)}, aug)
        # Should contain E' -> . E, E -> . E + T, E -> . T, T -> . T * F, T -> . F, F -> . ( E ), F -> . id
        self.assertEqual(len(I0), 7)
        prods_in_I0 = {it.prod_id for it in I0}
        self.assertEqual(prods_in_I0, {0, 1, 2, 3, 4, 5, 6})

    def test_lr0_goto_and_canonical_collection_size(self):
        generator = SLR1TableGenerator(self.grammar)
        states, transitions = generator.build_canonical_collection()
        # Textbook Dragon Book classic 12 LR(0) states
        self.assertEqual(len(states), 12)
        self.assertGreater(len(transitions), 0)

    def test_slr1_table_generation_no_conflicts(self):
        generator = SLR1TableGenerator(self.grammar)
        result = generator.generate()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.conflicts), 0)
        self.assertEqual(result.states_count, 12)

        # Check accept action in state where E' -> E .
        # Find which state contains (0, 1)
        accept_state = None
        for i, it_set in enumerate(result.item_sets):
            for raw_it in it_set["raw_items"]:
                if raw_it["prod_id"] == 0 and raw_it["dot"] == 1:
                    accept_state = i
                    break
        self.assertIsNotNone(accept_state)
        acts = result.action_table[accept_state]["$"]
        self.assertTrue(any(a.action_type == "accept" for a in acts))

    def test_slr1_parse_valid_inputs(self):
        parser = SLR1Parser(self.grammar)

        valid_cases = [
            "id",
            "id + id",
            "id * id + id",
            "( id + id ) * id",
            "( ( id ) )",
        ]

        for text in valid_cases:
            tokens, errs = tokenize_input_string(text, self.grammar.terminals)
            self.assertEqual(len(errs), 0, f"Tokenization failed for '{text}'")
            res = parser.parse(tokens)
            self.assertTrue(res.accepted, f"Failed to accept '{text}': {res.error}")
            self.assertIsNotNone(res.parse_tree)
            self.assertEqual(res.parse_tree.symbol, "E")
            self.assertGreater(len(res.trace), 0)

    def test_slr1_parse_invalid_inputs(self):
        parser = SLR1Parser(self.grammar)

        invalid_cases = [
            "id +",
            "( id + id",
            "id id",
            "+ id",
            "",
        ]

        for text in invalid_cases:
            tokens, errs = tokenize_input_string(text, self.grammar.terminals)
            res = parser.parse(tokens)
            self.assertFalse(res.accepted, f"Incorrectly accepted invalid input '{text}'")
            self.assertIsNotNone(res.error)

    def test_slr1_shift_reduce_conflict_detected(self):
        # Classic grammar with SLR(1) Shift/Reduce conflict:
        # S -> L = R | R
        # L -> * R | id
        # R -> L
        grammar_text = """
        S -> L = R | R
        L -> * R | id
        R -> L
        """
        grammar, _ = parse_grammar_text(grammar_text)
        self.assertIsNotNone(grammar)
        generator = SLR1TableGenerator(grammar)
        result = generator.generate()

        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.conflicts), 0)
        sr_conflicts = [c for c in result.conflicts if c.conflict_type == "Shift/Reduce"]
        self.assertGreater(len(sr_conflicts), 0)
        # Conflict is on symbol '='
        self.assertTrue(any(c.symbol == "=" for c in sr_conflicts))

    def test_slr1_epsilon_grammar(self):
        grammar_text = """
        S -> a A b
        A -> eps
        """
        grammar, _ = parse_grammar_text(grammar_text)
        self.assertIsNotNone(grammar)
        generator = SLR1TableGenerator(grammar)
        result = generator.generate()
        self.assertTrue(result.is_valid)

        parser = SLR1Parser(grammar)
        tokens, _ = tokenize_input_string("a b", grammar.terminals)
        res = parser.parse(tokens)
        self.assertTrue(res.accepted)
        self.assertEqual(res.parse_tree.symbol, "S")


if __name__ == "__main__":
    unittest.main()
