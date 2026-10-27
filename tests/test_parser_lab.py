"""
Tests for MiniLang-X Parser Lab Foundation (Phase 1)
Covers grammar parsing, validation diagnostics, FIRST & FOLLOW algorithms, and API endpoints.
"""

import unittest
from visualizer.app import app
from parser_lab.grammar import parse_grammar_text, EPSILON, END_MARKER
from parser_lab.validation import GrammarValidator
from parser_lab.first_follow import FirstFollowCalculator


class ParserLabGrammarTests(unittest.TestCase):
    """Tests for grammar text parsing and symbol tokenization."""

    def test_parse_expression_grammar(self):
        text = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
        """
        grammar, diagnostics = parse_grammar_text(text)
        self.assertIsNotNone(grammar)
        self.assertEqual(len(diagnostics), 0)
        self.assertEqual(grammar.start_symbol, "E")
        self.assertEqual(grammar.nonterminals, ["E", "T", "F"])
        self.assertEqual(grammar.terminals, ["+", "*", "(", ")", "id"])
        self.assertEqual(len(grammar.productions), 6)

    def test_parse_epsilon_aliases(self):
        text = """
        A -> a | eps
        B -> b | epsilon
        C -> c | ε
        D -> d |
        """
        grammar, _ = parse_grammar_text(text)
        self.assertIsNotNone(grammar)
        self.assertEqual(grammar.nonterminals, ["A", "B", "C", "D"])
        for prod in grammar.productions:
            if prod.rhs == (EPSILON,):
                self.assertTrue(prod.is_epsilon)

    def test_multi_character_terminals_and_quotes(self):
        text = """
        Stmt -> if Expr then Stmt | '=='
        """
        grammar, _ = parse_grammar_text(text)
        self.assertIsNotNone(grammar)
        self.assertIn("==", grammar.terminals)
        self.assertIn("if", grammar.terminals)
        self.assertIn("then", grammar.terminals)


class ParserLabValidationTests(unittest.TestCase):
    """Tests for grammar validation rules and diagnostics."""

    def test_empty_grammar(self):
        grammar, parse_diags = parse_grammar_text("")
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("empty" in d.message.lower() for d in result.diagnostics))

    def test_malformed_production_line_missing_arrow(self):
        text = "E E + T"
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing derivation arrow" in d.message.lower() for d in result.diagnostics))

    def test_missing_left_hand_side(self):
        text = "-> a b"
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing left-hand side" in d.message.lower() for d in result.diagnostics))

    def test_undefined_nonterminals(self):
        text = "S -> a A"  # 'A' is referenced but has no productions
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("undefined nonterminal 'a'" in d.message.lower() for d in result.diagnostics))

    def test_invalid_start_symbol(self):
        text = "S -> a"
        grammar, parse_diags = parse_grammar_text(text, start_symbol="NonExistent")
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("invalid start symbol" in d.message.lower() for d in result.diagnostics))

    def test_epsilon_mixed_with_symbols(self):
        text = "A -> a eps b"
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertFalse(result.valid)
        self.assertTrue(any("cannot be mixed" in d.message.lower() for d in result.diagnostics))

    def test_duplicate_production_normalization(self):
        text = """
        S -> a | a
        """
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertTrue(result.valid)  # Duplicate is a warning, not fatal
        self.assertTrue(any(d.severity == "warning" for d in result.diagnostics))
        self.assertEqual(len(grammar.productions), 1)

    def test_unreachable_nonterminal_warning(self):
        text = """
        S -> a
        Unused -> b
        """
        grammar, parse_diags = parse_grammar_text(text)
        result = GrammarValidator.validate(grammar, parse_diags)
        self.assertTrue(result.valid)
        self.assertTrue(any("unreachable" in d.message.lower() for d in result.diagnostics))


class ParserLabFirstFollowTests(unittest.TestCase):
    """Mathematical verification of FIRST and FOLLOW set computations."""

    def test_simple_nullable_grammar(self):
        # S -> a A, A -> b | ε
        text = """
        S -> a A
        A -> b | ε
        """
        grammar, diags = parse_grammar_text(text)
        val = GrammarValidator.validate(grammar, diags)
        self.assertTrue(val.valid)

        calc = FirstFollowCalculator(grammar)
        res = calc.compute()

        # Expected FIRST sets
        self.assertEqual(set(res.first["A"]), {"b", EPSILON})
        self.assertEqual(set(res.first["S"]), {"a"})
        self.assertTrue(res.nullable["A"])
        self.assertFalse(res.nullable["S"])

        # Expected FOLLOW sets: FOLLOW(S) = {$}, FOLLOW(A) = {$}
        self.assertEqual(set(res.follow["S"]), {END_MARKER})
        self.assertEqual(set(res.follow["A"]), {END_MARKER})

        # Invariants
        for nt in grammar.nonterminals:
            self.assertNotIn(EPSILON, res.follow[nt])
        self.assertIn(END_MARKER, res.follow[grammar.start_symbol])

    def test_expression_grammar_with_left_recursion(self):
        # Classic Dragon Book arithmetic grammar
        text = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
        """
        grammar, diags = parse_grammar_text(text)
        val = GrammarValidator.validate(grammar, diags)
        self.assertTrue(val.valid)

        calc = FirstFollowCalculator(grammar)
        res = calc.compute()

        # FIRST sets
        expected_first = {"(", "id"}
        self.assertEqual(set(res.first["F"]), expected_first)
        self.assertEqual(set(res.first["T"]), expected_first)
        self.assertEqual(set(res.first["E"]), expected_first)

        # None are nullable
        self.assertFalse(res.nullable["E"])
        self.assertFalse(res.nullable["T"])
        self.assertFalse(res.nullable["F"])

        # FOLLOW sets
        self.assertEqual(set(res.follow["E"]), {"+", ")", END_MARKER})
        self.assertEqual(set(res.follow["T"]), {"+", "*", ")", END_MARKER})
        self.assertEqual(set(res.follow["F"]), {"+", "*", ")", END_MARKER})

        # Invariants
        for nt in grammar.nonterminals:
            self.assertNotIn(EPSILON, res.follow[nt])
        self.assertIn(END_MARKER, res.follow["E"])

    def test_multiple_nullable_nonterminals(self):
        text = """
        S -> A B C
        A -> a | ε
        B -> b | ε
        C -> c | ε
        """
        grammar, diags = parse_grammar_text(text)
        val = GrammarValidator.validate(grammar, diags)
        self.assertTrue(val.valid)

        calc = FirstFollowCalculator(grammar)
        res = calc.compute()

        # All symbols are nullable
        self.assertTrue(res.nullable["A"])
        self.assertTrue(res.nullable["B"])
        self.assertTrue(res.nullable["C"])
        self.assertTrue(res.nullable["S"])

        self.assertEqual(set(res.first["A"]), {"a", EPSILON})
        self.assertEqual(set(res.first["B"]), {"b", EPSILON})
        self.assertEqual(set(res.first["C"]), {"c", EPSILON})
        self.assertEqual(set(res.first["S"]), {"a", "b", "c", EPSILON})

        # FOLLOW sets
        # FOLLOW(A) = FIRST(BC) \ {eps} U FOLLOW(S) = {b, c, $}
        self.assertEqual(set(res.follow["A"]), {"b", "c", END_MARKER})
        # FOLLOW(B) = FIRST(C) \ {eps} U FOLLOW(S) = {c, $}
        self.assertEqual(set(res.follow["B"]), {"c", END_MARKER})
        # FOLLOW(C) = FOLLOW(S) = {$}
        self.assertEqual(set(res.follow["C"]), {END_MARKER})
        self.assertEqual(set(res.follow["S"]), {END_MARKER})

    def test_indirect_recursion(self):
        text = """
        S -> A a
        A -> B b
        B -> S c | d
        """
        grammar, diags = parse_grammar_text(text)
        val = GrammarValidator.validate(grammar, diags)
        self.assertTrue(val.valid)

        calc = FirstFollowCalculator(grammar)
        res = calc.compute()

        # Both 'd' directly and indirectly from S can be first
        self.assertIn("d", res.first["B"])
        self.assertIn("d", res.first["A"])
        self.assertIn("d", res.first["S"])
        self.assertIn(END_MARKER, res.follow["S"])
        for nt in grammar.nonterminals:
            self.assertNotIn(EPSILON, res.follow[nt])


class ParserLabAPITests(unittest.TestCase):
    """Tests for Flask API endpoints (/api/parser-lab/*)."""

    def setUp(self):
        self.client = app.test_client()

    def test_validate_api_success(self):
        payload = {
            "grammar": "E -> E + T | T\nT -> id"
        }
        res = self.client.post("/api/parser-lab/validate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])
        self.assertEqual(data["nonterminals"], ["E", "T"])
        self.assertIn("id", data["terminals"])

    def test_validate_api_with_errors(self):
        payload = {
            "grammar": "S -> a B"  # Undefined B
        }
        res = self.client.post("/api/parser-lab/validate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["valid"])
        self.assertTrue(len(data["diagnostics"]) > 0)

    def test_first_follow_api_success(self):
        payload = {
            "grammar": "S -> a A\nA -> b | eps"
        }
        res = self.client.post("/api/parser-lab/first-follow", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])
        self.assertIn("first", data)
        self.assertIn("follow", data)
        self.assertEqual(set(data["first"]["S"]), {"a"})
        self.assertEqual(set(data["follow"]["S"]), {"$"})

    def test_first_follow_api_with_fatal_errors(self):
        payload = {
            "grammar": "Malformed line without arrow"
        }
        res = self.client.post("/api/parser-lab/first-follow", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["valid"])
        self.assertEqual(data["first"], {})
        self.assertEqual(data["follow"], {})

    def test_api_malformed_json_requests(self):
        # Non-JSON content type or malformed body
        res = self.client.post("/api/parser-lab/validate", data="not a json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])

        res = self.client.post("/api/parser-lab/first-follow", data="not a json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])


if __name__ == "__main__":
    unittest.main()
