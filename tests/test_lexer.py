import unittest

from lexer.lexer import Lexer, LexicalError
from lexer.statistics import calculate_token_statistics
from lexer.token import TokenType
from visualizer.app import app


class LexerTests(unittest.TestCase):
    def test_identifiers_and_keywords(self):
        tokens = Lexer("int count_1; print(count_1);").tokenize()

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.INT,
                TokenType.IDENTIFIER,
                TokenType.SEMICOLON,
                TokenType.PRINT,
                TokenType.LPAREN,
                TokenType.IDENTIFIER,
                TokenType.RPAREN,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ],
        )
        self.assertEqual(tokens[1].value, "count_1")

    def test_integer_float_and_string_literals(self):
        tokens = Lexer('42 3.14 "hello" true').tokenize()

        self.assertEqual(
            [token.type for token in tokens[:-1]],
            [
                TokenType.INTEGER,
                TokenType.FLOAT_LITERAL,
                TokenType.STRING_LITERAL,
                TokenType.TRUE,
            ],
        )
        self.assertEqual([token.value for token in tokens[:3]], ["42", "3.14", "hello"])

    def test_arithmetic_and_comparison_operators(self):
        tokens = Lexer("+ - * / = == != < <= > >= !").tokenize()

        self.assertEqual(
            [token.type for token in tokens[:-1]],
            [
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.MULTIPLY,
                TokenType.DIVIDE,
                TokenType.ASSIGN,
                TokenType.EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.NOT,
            ],
        )

    def test_separators_and_positions(self):
        tokens = Lexer("int value = 42;\nprint(value);").tokenize()

        self.assertEqual(
            [token.type for token in tokens if token.type in {
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.LBRACE,
                TokenType.RBRACE,
                TokenType.SEMICOLON,
            }],
            [
                TokenType.SEMICOLON,
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.SEMICOLON,
            ],
        )
        self.assertEqual((tokens[0].line, tokens[0].column), (1, 1))
        self.assertEqual((tokens[1].line, tokens[1].column), (1, 5))
        self.assertEqual((tokens[5].line, tokens[5].column), (2, 1))
        self.assertEqual((tokens[-1].line, tokens[-1].column), (2, 14))

    def test_invalid_character_reports_location_and_explanation(self):
        with self.assertRaises(LexicalError) as caught:
            Lexer("int x = 1;\n  @").tokenize()

        message = str(caught.exception)
        self.assertIn("Lexical Error", message)
        self.assertIn("Line: 2", message)
        self.assertIn("Column: 3", message)
        self.assertIn("Unexpected character: @", message)
        self.assertIn("not part of the MiniLang-X language", message)

    def test_unterminated_string_is_a_lexical_error(self):
        with self.assertRaises(LexicalError) as caught:
            Lexer('"unterminated').tokenize()

        self.assertIn("Unterminated string", str(caught.exception))
        self.assertIn("Line: 1", str(caught.exception))
        self.assertIn("Column: 1", str(caught.exception))

    def test_statistics_exclude_eof_and_include_skipped_comments(self):
        lexer = Lexer("int x = 1 + 2; // note\nprint(x);")
        tokens = lexer.tokenize()

        statistics = calculate_token_statistics(
            tokens,
            comment_count=lexer.comment_count,
        )

        self.assertEqual(
            statistics,
            {
                "total_tokens": 12,
                "identifiers": 2,
                "keywords": 2,
                "literals": 2,
                "operators": 2,
                "separators": 4,
                "comments": 1,
            },
        )

    def test_token_api_returns_existing_tokens_and_statistics(self):
        response = app.test_client().post(
            "/api/tokens",
            json={"source": "int x = 2; // comment"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["tokens"][0]["type"], "INT")
        self.assertEqual(data["tokens"][0]["line"], 1)
        self.assertEqual(data["tokens"][0]["column"], 1)
        self.assertEqual(data["tokens"][-1]["type"], "EOF")
        self.assertEqual(data["statistics"]["total_tokens"], 5)
        self.assertEqual(data["statistics"]["comments"], 1)

    def test_token_api_returns_readable_lexical_error(self):
        response = app.test_client().post(
            "/api/tokens",
            json={"source": "@"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Lexical Error", data["error"])
        self.assertIn("Line: 1", data["error"])
        self.assertIn("Column: 1", data["error"])
        self.assertIn("Unexpected character: @", data["error"])
        self.assertNotIn("Traceback", data["error"])


if __name__ == "__main__":
    unittest.main()
