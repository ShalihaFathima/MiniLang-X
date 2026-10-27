"""
Verification tests specifically validating the Step 3 requirements for Phase 2:
Grammar:
  E -> T EPrime
  EPrime -> + T EPrime | ε
  T -> id
Input:
  id + id (accepted by LL(1) and RD)
  id      (accepted)
  id +    (rejected)
"""

import unittest
from parser_lab.grammar import parse_grammar_text
from parser_lab.validation import GrammarValidator
from parser_lab.first_follow import FirstFollowCalculator
from parser_lab.ll1 import LL1TableGenerator, LL1Parser
from parser_lab.recursive_descent import RecursiveDescentParser
from visualizer.app import app


class Phase2Step3VerificationTests(unittest.TestCase):
    def setUp(self):
        self.grammar_text = (
            "E -> T EPrime\n"
            "EPrime -> + T EPrime | ε\n"
            "T -> id"
        )
        self.grammar, self.diagnostics = parse_grammar_text(self.grammar_text, start_symbol="E")
        self.client = app.test_client()

    def test_grammar_validation_succeeds(self):
        result = GrammarValidator.validate(self.grammar, self.diagnostics)
        self.assertTrue(result.valid)
        errors = [d for d in result.diagnostics if d.severity == "error"]
        self.assertEqual(len(errors), 0)

    def test_first_sets(self):
        calc = FirstFollowCalculator(self.grammar)
        res = calc.compute()
        self.assertEqual(set(res.first["E"]), {"id"})
        self.assertEqual(set(res.first["EPrime"]), {"+", "ε"})
        self.assertEqual(set(res.first["T"]), {"id"})

    def test_follow_sets(self):
        calc = FirstFollowCalculator(self.grammar)
        res = calc.compute()
        self.assertEqual(set(res.follow["E"]), {"$"})
        self.assertEqual(set(res.follow["EPrime"]), {"$"})
        self.assertEqual(set(res.follow["T"]), {"+", "$"})

    def test_ll1_table_generation_no_conflicts(self):
        gen = LL1TableGenerator(self.grammar)
        res = gen.generate()
        self.assertTrue(res.is_ll1)
        self.assertEqual(len(res.conflicts), 0)

        # M[E, id] = E -> T EPrime
        self.assertEqual(len(res.table["E"]["id"]), 1)
        self.assertEqual(res.table["E"]["id"][0].rhs, ("T", "EPrime"))

        # M[EPrime, +] = EPrime -> + T EPrime
        self.assertEqual(len(res.table["EPrime"]["+"]), 1)
        self.assertEqual(res.table["EPrime"]["+"][0].rhs, ("+", "T", "EPrime"))

        # M[EPrime, $] = EPrime -> ε
        self.assertEqual(len(res.table["EPrime"]["$"]), 1)
        self.assertTrue(res.table["EPrime"]["$"][0].is_epsilon)

        # M[T, id] = T -> id
        self.assertEqual(len(res.table["T"]["id"]), 1)
        self.assertEqual(res.table["T"]["id"][0].rhs, ("id",))

    def test_ll1_parsing_accepts_id_plus_id(self):
        parser = LL1Parser(self.grammar)
        res = parser.parse(["id", "+", "id"])
        self.assertTrue(res.accepted)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.parse_tree)
        self.assertGreater(len(res.trace), 0)
        # Check trace contains stack, remaining_input, and action
        for step in res.trace:
            self.assertIsNotNone(step.stack)
            self.assertIsNotNone(step.remaining_input)
            self.assertTrue(len(step.action) > 0)

    def test_recursive_descent_accepts_id_plus_id(self):
        parser = RecursiveDescentParser(self.grammar)
        res = parser.parse(["id", "+", "id"])
        self.assertTrue(res.accepted)
        self.assertFalse(res.has_left_recursion)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.parse_tree)
        self.assertGreater(len(res.trace), 0)

    def test_single_id_accepted(self):
        ll1 = LL1Parser(self.grammar).parse(["id"])
        self.assertTrue(ll1.accepted)

        rd = RecursiveDescentParser(self.grammar).parse(["id"])
        self.assertTrue(rd.accepted)

    def test_id_plus_rejected(self):
        ll1 = LL1Parser(self.grammar).parse(["id", "+"])
        self.assertFalse(ll1.accepted)
        self.assertIn("Syntax Error", ll1.error)

        rd = RecursiveDescentParser(self.grammar).parse(["id", "+"])
        self.assertFalse(rd.accepted)
        self.assertIn("Syntax Error", rd.error)

    def test_api_endpoints_for_step3(self):
        # 1. /api/parser-lab/ll1/table
        res = self.client.post("/api/parser-lab/ll1/table", json={
            "grammar": self.grammar_text,
            "start_symbol": "E"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["valid"])
        self.assertTrue(data["is_ll1"])
        self.assertEqual(data["conflicts"], [])

        # 2. /api/parser-lab/ll1/parse for id + id
        res = self.client.post("/api/parser-lab/ll1/parse", json={
            "grammar": self.grammar_text,
            "start_symbol": "E",
            "input": "id + id"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["accepted"])
        self.assertIsNotNone(data["parse_tree"])
        self.assertGreater(len(data["trace"]), 0)

        # 3. /api/parser-lab/recursive-descent/parse for id + id
        res = self.client.post("/api/parser-lab/recursive-descent/parse", json={
            "grammar": self.grammar_text,
            "start_symbol": "E",
            "input": "id + id"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["accepted"])
        self.assertFalse(data["has_left_recursion"])
        self.assertIsNotNone(data["parse_tree"])

        # 4. /api/parser-lab/ll1/parse for id + (should fail gracefully)
        res = self.client.post("/api/parser-lab/ll1/parse", json={
            "grammar": self.grammar_text,
            "start_symbol": "E",
            "input": "id +"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data["accepted"])
        self.assertIsNotNone(data["error"])


if __name__ == "__main__":
    unittest.main()
