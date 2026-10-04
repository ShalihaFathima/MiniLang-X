import unittest

from visualizer.app import app
from visualizer.compiler_bridge import semantic_source


class SemanticTests(unittest.TestCase):
    def test_valid_declaration_and_identifier_use(self):
        result = semantic_source("int x = 10; print(x);")

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["symbols"]), 1)
        self.assertEqual(result["symbols"][0]["name"], "x")
        self.assertEqual(result["symbols"][0]["data_type"], "int")
        self.assertTrue(result["symbols"][0]["initialized"])
        self.assertEqual(
            (result["symbols"][0]["line"], result["symbols"][0]["column"]),
            (1, 5),
        )
        self.assertEqual(result["statistics"]["identifier_use_count"], 1)

    def test_undeclared_variable_reports_actual_location(self):
        source = "int x = y + 10;\nprint(x);"
        result = semantic_source(source)

        self.assertFalse(result["valid"])
        error = result["errors"][0]
        self.assertEqual(error["type"], "Undeclared Variable")
        self.assertEqual(error["message"], "Variable 'y' is not declared")
        self.assertEqual((error["line"], error["column"]), (1, 9))
        self.assertIn("int x = y + 10;", error["source_context"])

    def test_duplicate_declaration_remains_rejected(self):
        result = semantic_source("int x = 1;\nint x = 2;")

        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["type"], "Duplicate Declaration")
        self.assertEqual((result["errors"][0]["line"], result["errors"][0]["column"]), (2, 5))

    def test_valid_assignment_updates_initialization(self):
        result = semantic_source("int x;\nx = 4;")

        self.assertTrue(result["valid"])
        self.assertTrue(result["symbols"][0]["initialized"])

    def test_existing_type_compatibility_is_preserved(self):
        self.assertTrue(semantic_source("float x = 1;")["valid"])

        result = semantic_source('int x = "text";')
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["type"], "Type Mismatch")

    def test_invalid_condition_reports_control_statement_location(self):
        result = semantic_source("if (1) { print(1); }")

        self.assertFalse(result["valid"])
        error = result["errors"][0]
        self.assertEqual(error["type"], "Invalid Condition")
        self.assertEqual((error["line"], error["column"]), (1, 1))

    def test_symbol_table_retains_real_nested_block_symbols(self):
        result = semantic_source("int x = 1; if (true) { int y = 2; print(y); }")

        self.assertTrue(result["valid"])
        self.assertEqual(
            [(symbol["name"], symbol["scope_level"]) for symbol in result["symbols"]],
            [("x", 0), ("y", 1)],
        )
        self.assertEqual(result["statistics"]["scope_count"], 2)

    def test_semantic_statistics_report_actual_analysis_data(self):
        result = semantic_source("int x = 1; print(x);")

        self.assertEqual(
            result["statistics"],
            {
                "symbol_count": 1,
                "declaration_count": 1,
                "identifier_use_count": 1,
                "scope_count": 1,
                "error_count": 0,
                "initialized_count": 1,
                "variables_by_type": {"int": 1},
            },
        )

    def test_api_preserves_fields_and_adds_statistics(self):
        response = app.test_client().post(
            "/api/semantic",
            json={"source": "int x = 10; print(x);"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])
        self.assertIn("symbols", data)
        self.assertIn("message", data)
        self.assertIn("statistics", data)
        self.assertEqual(data["statistics"]["symbol_count"], 1)

    def test_api_returns_structured_semantic_error(self):
        response = app.test_client().post(
            "/api/semantic",
            json={"source": "int x = y;"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["valid"])
        self.assertIn("Variable 'y' is not declared", data["error"])
        self.assertEqual(data["error_details"]["line"], 1)
        self.assertEqual(data["error_details"]["column"], 9)
        self.assertEqual(data["statistics"]["error_count"], 1)
        self.assertNotIn("Traceback", data["error"])


if __name__ == "__main__":
    unittest.main()
