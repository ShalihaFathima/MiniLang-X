import unittest

from lexer.lexer import Lexer
from parser.parser import Parser, ParserSyntaxError
from syntax_tree.statistics import calculate_ast_statistics
from visualizer.app import app
from visualizer.compiler_bridge import parse_source


class ParserTests(unittest.TestCase):
    def parse(self, source):
        return Parser(Lexer(source).tokenize(), source=source).parse()

    def test_arithmetic_expression_obeys_operator_precedence(self):
        ast = parse_source("int x = 10 + 20 * 3;")
        addition = ast["children"][0]["children"][0]

        self.assertEqual(addition["type"], "BinaryExpression")
        self.assertEqual(addition["operator"], "+")
        self.assertEqual(addition["children"][0]["value"], "10")
        multiplication = addition["children"][1]
        self.assertEqual(multiplication["type"], "BinaryExpression")
        self.assertEqual(multiplication["operator"], "*")
        self.assertEqual(
            [child["value"] for child in multiplication["children"]],
            ["20", "3"],
        )

    def test_variable_declaration_preserves_type_and_name(self):
        ast = parse_source("float amount = 2.5;")
        declaration = ast["children"][0]

        self.assertEqual(declaration["type"], "VarDeclaration")
        self.assertEqual(declaration["name"], "amount")
        self.assertEqual(declaration["data_type"], "float")

    def test_conditional_and_print_statements(self):
        ast = parse_source("if (true) { print(1); }")
        conditional = ast["children"][0]

        self.assertEqual(conditional["type"], "IfStatement")
        self.assertEqual(
            conditional["children"][1]["children"][0]["type"],
            "PrintStatement",
        )

    def test_invalid_syntax_reports_location_expected_token_and_context(self):
        source = "int x = 10 + );"

        with self.assertRaises(ParserSyntaxError) as caught:
            self.parse(source)

        error = caught.exception
        self.assertEqual((error.line, error.column), (1, 14))
        self.assertEqual(error.expected, "expression")
        self.assertIn("Syntax Error", str(error))
        self.assertIn("Unexpected token: ')' (RPAREN)", str(error))
        self.assertIn("Source:", str(error))
        self.assertIn("^", error.source_context)

    def test_eof_syntax_error_after_trailing_newline_has_context(self):
        source = "print(\n"

        with self.assertRaises(ParserSyntaxError) as caught:
            self.parse(source)

        error = caught.exception
        self.assertEqual((error.line, error.column), (2, 1))
        self.assertEqual(error.source_context, "\n^")

    def test_ast_statistics_count_real_nodes(self):
        ast = self.parse("int x = 10 + 20 * 3; print(x);")

        self.assertEqual(
            calculate_ast_statistics(ast),
            {
                "total_nodes": 9,
                "max_depth": 5,
                "statement_count": 2,
                "expression_count": 6,
                "identifier_count": 1,
                "literal_count": 3,
                "operator_count": 2,
            },
        )

    def test_parse_api_returns_ast_statistics(self):
        response = app.test_client().post(
            "/api/parse",
            json={"source": "int x = 10 + 20 * 3; print(x);"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["ast"]["type"], "Program")
        self.assertEqual(data["statistics"]["token_count"], 14)
        self.assertEqual(data["statistics"]["total_nodes"], 9)
        self.assertEqual(data["statistics"]["operator_count"], 2)

    def test_parse_api_returns_structured_syntax_error(self):
        response = app.test_client().post(
            "/api/parse",
            json={"source": "int x = 10 + );"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["details"]["type"], "Syntax Error")
        self.assertEqual(data["details"]["line"], 1)
        self.assertEqual(data["details"]["column"], 14)
        self.assertEqual(data["details"]["expected"], "expression")
        self.assertIn("Source:", data["error"])
        self.assertNotIn("Traceback", data["error"])


if __name__ == "__main__":
    unittest.main()
