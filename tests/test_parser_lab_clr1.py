"""
Unit tests for Canonical LR(1) (CLR(1)) parsing:
LR(1) closure, lookahead propagation, canonical LR(1) state construction,
ACTION/GOTO table generation, conflict detection, parse traces, and parse trees.
"""

import unittest

from parser_lab.grammar import parse_grammar_text
from parser_lab.lr_common import LR1Item, AugmentedGrammar
from parser_lab.clr1 import lr1_closure, CLR1TableGenerator, CLR1Parser
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.tokenizer import tokenize_input_string


class CLR1ParsingTests(unittest.TestCase):
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

    def test_lr1_closure_and_lookahead_propagation(self):
        aug = AugmentedGrammar(self.grammar)
        calc = FirstFollowCalculator(self.grammar)
        raw_first = calc.compute_first()

        initial_item = LR1Item(0, 0, "$")
        I0 = lr1_closure({initial_item}, aug, raw_first, calc)

        # In I0:
        # [E' -> . E, $]
        # [E -> . E + T, $] and [E -> . E + T, +]
        # [E -> . T, $] and [E -> . T, +]
        # Check that items carry correct lookaheads
        e_prime_items = [it for it in I0 if it.prod_id == 0]
        self.assertEqual(len(e_prime_items), 1)
        self.assertEqual(e_prime_items[0].lookahead, "$")

        # Plus is propagated to E -> . E + T because E is followed by + T
        plus_items = [it for it in I0 if it.lookahead == "+"]
        self.assertGreater(len(plus_items), 0)

    def test_classic_lr1_not_lalr1_has_no_conflicts_in_clr1(self):
        generator = CLR1TableGenerator(self.classic_grammar)
        result = generator.generate()

        # CLR(1) must parse this grammar WITHOUT conflicts!
        self.assertTrue(result.is_valid, f"Expected CLR(1) to be conflict-free, got: {result.conflicts}")
        self.assertEqual(len(result.conflicts), 0)

        # Parse all 4 valid sentences
        parser = CLR1Parser(self.classic_grammar)
        for sentence in ["a c d", "b c e", "a c e", "b c d"]:
            tokens, errs = tokenize_input_string(sentence, self.classic_grammar.terminals)
            self.assertEqual(len(errs), 0)
            res = parser.parse(tokens)
            self.assertTrue(res.accepted, f"Failed on '{sentence}': {res.error}")
            self.assertEqual(res.parse_tree.symbol, "S")

    def test_clr1_expression_grammar_parsing(self):
        generator = CLR1TableGenerator(self.grammar)
        result = generator.generate()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.conflicts), 0)

        parser = CLR1Parser(self.grammar)

        # Valid inputs
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

        # Invalid inputs
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

    def test_clr1_ambiguous_grammar_conflicts(self):
        # Ambiguous grammar S -> S + S | id
        grammar_text = "S -> S + S | id"
        grammar, _ = parse_grammar_text(grammar_text)
        generator = CLR1TableGenerator(grammar)
        result = generator.generate()

        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.conflicts), 0)
        sr = [c for c in result.conflicts if c.conflict_type == "Shift/Reduce"]
        self.assertGreater(len(sr), 0)


if __name__ == "__main__":
    unittest.main()
