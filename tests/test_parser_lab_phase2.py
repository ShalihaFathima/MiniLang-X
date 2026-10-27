"""
MiniLang-X Parser Lab — Phase 2 Automated Tests
Top-Down Parsing: LL(1) Predictive Parsing Table, Table-Driven Parser,
Recursive Descent with Left-Recursion Detection, and API Integration.
"""

import unittest
from visualizer.app import app
from parser_lab.grammar import parse_grammar_text, EPSILON, END_MARKER
from parser_lab.tokenizer import tokenize_input_string
from parser_lab.ll1 import LL1TableGenerator, LL1Parser
from parser_lab.recursive_descent import (
    RecursiveDescentParser,
    LeftRecursionDetector,
)


class LL1TableGenerationTests(unittest.TestCase):
    """Tests for LL(1) parsing table construction and conflict detection."""

    def setUp(self):
        # Known LL(1) arithmetic grammar
        self.ll1_grammar_text = """
        E -> T EPrime
        EPrime -> + T EPrime | eps
        T -> F TPrime
        TPrime -> * F TPrime | eps
        F -> ( E ) | id
        """
        self.grammar, _ = parse_grammar_text(self.ll1_grammar_text)
        self.assertIsNotNone(self.grammar)

    def test_ll1_table_entries_for_known_grammar(self):
        generator = LL1TableGenerator(self.grammar)
        res = generator.generate()

        self.assertTrue(res.is_ll1)
        self.assertEqual(len(res.conflicts), 0)

        # M[E, id] should contain E -> T EPrime
        e_id_prods = res.table["E"]["id"]
        self.assertEqual(len(e_id_prods), 1)
        self.assertEqual(e_id_prods[0].lhs, "E")
        self.assertEqual(e_id_prods[0].rhs, ("T", "EPrime"))

        # M[E, (] should contain E -> T EPrime
        e_paren_prods = res.table["E"]["("]
        self.assertEqual(len(e_paren_prods), 1)

        # M[E, +] should be empty
        self.assertEqual(len(res.table["E"]["+"]), 0)

    def test_epsilon_production_using_follow_sets(self):
        generator = LL1TableGenerator(self.grammar)
        res = generator.generate()

        # EPrime -> eps is nullable, so it should be mapped in FOLLOW(EPrime) = { ')', '$' }
        # FIRST(+) has EPrime -> + T EPrime
        plus_prods = res.table["EPrime"]["+"]
        self.assertEqual(len(plus_prods), 1)
        self.assertEqual(plus_prods[0].rhs, ("+", "T", "EPrime"))

        dollar_prods = res.table["EPrime"][END_MARKER]
        self.assertEqual(len(dollar_prods), 1)
        self.assertEqual(dollar_prods[0].rhs, (EPSILON,))

        rparen_prods = res.table["EPrime"][")"]
        self.assertEqual(len(rparen_prods), 1)
        self.assertEqual(rparen_prods[0].rhs, (EPSILON,))

    def test_first_first_conflict_detection(self):
        # Non-LL(1) grammar with FIRST/FIRST conflict
        text = """
        S -> a B | a C
        B -> b
        C -> c
        """
        grammar, _ = parse_grammar_text(text)
        generator = LL1TableGenerator(grammar)
        res = generator.generate()

        self.assertFalse(res.is_ll1)
        self.assertTrue(len(res.conflicts) > 0)
        self.assertEqual(res.conflicts[0].nonterminal, "S")
        self.assertEqual(res.conflicts[0].terminal, "a")
        self.assertEqual(res.conflicts[0].conflict_type, "FIRST/FIRST")

    def test_first_follow_conflict_detection(self):
        # Non-LL(1) grammar with FIRST/FOLLOW conflict
        text = """
        S -> A a
        A -> a | eps
        """
        grammar, _ = parse_grammar_text(text)
        generator = LL1TableGenerator(grammar)
        res = generator.generate()

        self.assertFalse(res.is_ll1)
        self.assertTrue(len(res.conflicts) > 0)
        # In A, 'a' is in FIRST(a) and also in FOLLOW(A) since S -> A a
        a_conflicts = [c for c in res.conflicts if c.nonterminal == "A" and c.terminal == "a"]
        self.assertTrue(len(a_conflicts) > 0)
        self.assertEqual(a_conflicts[0].conflict_type, "FIRST/FOLLOW")


class LL1ParsingTests(unittest.TestCase):
    """Tests for LL(1) table-driven stack parser execution."""

    def setUp(self):
        text = """
        E -> T EPrime
        EPrime -> + T EPrime | eps
        T -> id
        """
        self.grammar, _ = parse_grammar_text(text)
        self.parser = LL1Parser(self.grammar)

    def test_valid_input_accepted(self):
        tokens, errs = tokenize_input_string("id + id", self.grammar.terminals)
        self.assertEqual(errs, [])
        res = self.parser.parse(tokens)

        self.assertTrue(res.accepted)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.parse_tree)
        self.assertEqual(res.parse_tree.symbol, "E")
        self.assertTrue(len(res.trace) > 0)
        self.assertEqual(res.trace[-1].status, "accept")

    def test_invalid_input_terminal_mismatch(self):
        tokens, _ = tokenize_input_string("id + +", self.grammar.terminals)
        res = self.parser.parse(tokens)

        self.assertFalse(res.accepted)
        self.assertIsNotNone(res.error)
        self.assertTrue(any("Syntax Error" in step.action for step in res.trace))

    def test_missing_table_entry(self):
        # Input starts with '+' which is not in FIRST(E)
        tokens, _ = tokenize_input_string("+ id", self.grammar.terminals)
        res = self.parser.parse(tokens)

        self.assertFalse(res.accepted)
        self.assertIn("No LL(1) table entry", res.error)

    def test_empty_input_for_nullable_grammar(self):
        text = """
        S -> a | eps
        """
        grammar, _ = parse_grammar_text(text)
        parser = LL1Parser(grammar)
        res = parser.parse([])

        self.assertTrue(res.accepted)
        self.assertEqual(len(res.parse_tree.children), 1)
        self.assertEqual(res.parse_tree.children[0].symbol, EPSILON)


class RecursiveDescentParsingTests(unittest.TestCase):
    """Tests for Recursive Descent parser and left-recursion detection."""

    def test_simple_recursive_descent_success(self):
        text = """
        E -> T EPrime
        EPrime -> + T EPrime | eps
        T -> id
        """
        grammar, _ = parse_grammar_text(text)
        parser = RecursiveDescentParser(grammar)
        self.assertFalse(parser.left_recursion.has_left_recursion)

        tokens, _ = tokenize_input_string("id + id", grammar.terminals)
        res = parser.parse(tokens)

        self.assertTrue(res.accepted)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.parse_tree)
        self.assertEqual(res.parse_tree.symbol, "E")

    def test_recursive_descent_with_epsilon(self):
        text = """
        S -> a A
        A -> b | eps
        """
        grammar, _ = parse_grammar_text(text)
        parser = RecursiveDescentParser(grammar)

        # Test S -> a A where A derives epsilon (input is just 'a')
        tokens, _ = tokenize_input_string("a", grammar.terminals)
        res = parser.parse(tokens)
        self.assertTrue(res.accepted)
        self.assertEqual(len(res.parse_tree.children), 2)
        self.assertEqual(res.parse_tree.children[0].symbol, "a")
        self.assertEqual(res.parse_tree.children[1].symbol, "A")

    def test_direct_left_recursion_detection(self):
        text = """
        E -> E + T | T
        T -> id
        """
        grammar, _ = parse_grammar_text(text)
        detector = LeftRecursionDetector(grammar)
        report = detector.analyze()

        self.assertTrue(report.has_left_recursion)
        self.assertIn("E", report.direct_left_recursion)
        self.assertIsNotNone(report.explanation)

    def test_indirect_left_recursion_detection(self):
        text = """
        S -> A a
        A -> B b
        B -> S c | d
        """
        grammar, _ = parse_grammar_text(text)
        detector = LeftRecursionDetector(grammar)
        report = detector.analyze()

        self.assertTrue(report.has_left_recursion)
        self.assertTrue(len(report.indirect_left_recursion) > 0)
        self.assertIsNotNone(report.explanation)

    def test_safeguard_against_infinite_recursion(self):
        # A directly left-recursive grammar run with low max_depth
        text = """
        E -> E + T | T
        T -> id
        """
        grammar, _ = parse_grammar_text(text)
        parser = RecursiveDescentParser(grammar, max_depth=15, max_steps=100)
        res = parser.parse(["id", "+", "id"])

        self.assertFalse(res.accepted)
        self.assertTrue(res.has_left_recursion)
        self.assertTrue("limit" in res.error.lower() or "recursion" in res.error.lower())

    def test_unconsumed_input_rejected(self):
        text = """
        S -> id
        """
        grammar, _ = parse_grammar_text(text)
        parser = RecursiveDescentParser(grammar)
        res = parser.parse(["id", "id"])

        self.assertFalse(res.accepted)
        self.assertIn("Unconsumed input", res.error)


class ParserLabPhase2APITests(unittest.TestCase):
    """Integration tests for Phase 2 Flask endpoints."""

    def setUp(self):
        self.client = app.test_client()
        self.grammar = """
        E -> T EPrime
        EPrime -> + T EPrime | eps
        T -> id
        """

    def test_api_ll1_table_generation(self):
        payload = {"grammar": self.grammar}
        res = self.client.post("/api/parser-lab/ll1/table", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])
        self.assertTrue(data["is_ll1"])
        self.assertIn("table", data)
        self.assertIn("E", data["table"])
        self.assertIn("id", data["table"]["E"])

    def test_api_ll1_parse_valid(self):
        payload = {
            "grammar": self.grammar,
            "input": "id + id"
        }
        res = self.client.post("/api/parser-lab/ll1/parse", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertTrue(data["accepted"])
        self.assertEqual(data["tokens"], ["id", "+", "id"])
        self.assertTrue(len(data["trace"]) > 0)
        self.assertIsNotNone(data["parse_tree"])

    def test_api_ll1_parse_invalid(self):
        payload = {
            "grammar": self.grammar,
            "input": "id + +"
        }
        res = self.client.post("/api/parser-lab/ll1/parse", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertFalse(data["accepted"])
        self.assertIsNotNone(data["error"])

    def test_api_recursive_descent_parse_valid(self):
        payload = {
            "grammar": self.grammar,
            "input": "id + id"
        }
        res = self.client.post("/api/parser-lab/recursive-descent/parse", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertTrue(data["accepted"])
        self.assertFalse(data["has_left_recursion"])
        self.assertIsNotNone(data["parse_tree"])

    def test_api_recursive_descent_left_recursion_warning(self):
        payload = {
            "grammar": "E -> E + T | T\nT -> id",
            "input": "id"
        }
        res = self.client.post("/api/parser-lab/recursive-descent/parse", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertTrue(data["success"])
        self.assertTrue(data["has_left_recursion"])
        self.assertIsNotNone(data["left_recursion"])


if __name__ == "__main__":
    unittest.main()
