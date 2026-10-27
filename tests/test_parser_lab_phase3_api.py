"""
MiniLang-X Parser Lab — Phase 3 API Automated Tests
Verifies endpoints for SLR(1), CLR(1), and LALR(1):
item sets, parsing tables, stack trace parsing, malformed inputs, and conflict diagnostics.
"""

import json
import unittest

from visualizer.app import app


class ParserLabPhase3APITests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.expr_grammar = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
        """
        self.classic_grammar = """
        S -> a A d | b A e | a B e | b B d
        A -> c
        B -> c
        """

    def test_api_slr1_items(self):
        resp = self.client.post(
            "/api/parser-lab/slr1/items",
            data=json.dumps({"grammar": self.expr_grammar}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])
        self.assertEqual(data["states_count"], 12)
        self.assertEqual(len(data["item_sets"]), 12)
        self.assertGreater(len(data["transitions"]), 0)

    def test_api_slr1_table(self):
        resp = self.client.post(
            "/api/parser-lab/slr1/table",
            data=json.dumps({"grammar": self.expr_grammar}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_slr1"])
        self.assertEqual(len(data["conflicts"]), 0)
        self.assertIn("action_table", data)
        self.assertIn("goto_table", data)

    def test_api_slr1_parse_valid(self):
        resp = self.client.post(
            "/api/parser-lab/slr1/parse",
            data=json.dumps({
                "grammar": self.expr_grammar,
                "input": "id + id * id",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["accepted"])
        self.assertGreater(len(data["trace"]), 0)
        self.assertIsNotNone(data["parse_tree"])
        self.assertEqual(data["parse_tree"]["symbol"], "E")

    def test_api_slr1_parse_invalid(self):
        resp = self.client.post(
            "/api/parser-lab/slr1/parse",
            data=json.dumps({
                "grammar": self.expr_grammar,
                "input": "id +",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["accepted"])
        self.assertIsNotNone(data["error"])

    def test_api_clr1_items_and_table(self):
        resp = self.client.post(
            "/api/parser-lab/clr1/table",
            data=json.dumps({"grammar": self.classic_grammar}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_clr1"])
        self.assertEqual(len(data["conflicts"]), 0)

    def test_api_clr1_parse(self):
        resp = self.client.post(
            "/api/parser-lab/clr1/parse",
            data=json.dumps({
                "grammar": self.classic_grammar,
                "input": "a c d",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["accepted"])

    def test_api_lalr1_table_conflict_on_classic_grammar(self):
        resp = self.client.post(
            "/api/parser-lab/lalr1/table",
            data=json.dumps({"grammar": self.classic_grammar}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_lalr1"])
        self.assertGreater(len(data["conflicts"]), 0)
        self.assertIsNotNone(data["merged_states_info"])

    def test_api_lalr1_parse_expression(self):
        resp = self.client.post(
            "/api/parser-lab/lalr1/parse",
            data=json.dumps({
                "grammar": self.expr_grammar,
                "input": "( id + id ) * id",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["accepted"])
        self.assertEqual(data["parse_tree"]["symbol"], "E")

    def test_api_malformed_requests(self):
        # Non-JSON request
        resp = self.client.post(
            "/api/parser-lab/slr1/table",
            data="not a json",
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, 400)

        # Malformed grammar syntax
        resp = self.client.post(
            "/api/parser-lab/slr1/table",
            data=json.dumps({"grammar": "InvalidGrammarWithoutArrow"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["valid"])
        self.assertGreater(len(data["diagnostics"]), 0)


if __name__ == "__main__":
    unittest.main()
