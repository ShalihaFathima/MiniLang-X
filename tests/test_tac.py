import unittest

from ir.generator import TACGenerator
from ir.statistics import calculate_tac_statistics
from lexer.lexer import Lexer
from parser.parser import Parser
from visualizer.app import app
from visualizer.compiler_bridge import tac_source


def generate_tac(source):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens, source=source).parse()
    return TACGenerator().generate(ast)


class TACTests(unittest.TestCase):
    def test_simple_assignment_uses_existing_instruction_fields(self):
        tac = generate_tac("int x = 1;")

        self.assertEqual(len(tac.instructions), 1)
        instruction = tac.instructions[0]
        self.assertEqual(instruction.operation, "ASSIGN")
        self.assertEqual(instruction.result, "x")
        self.assertEqual(instruction.arg1, "1")
        self.assertIsNone(instruction.arg2)

    def test_arithmetic_and_precedence_generate_temporaries(self):
        tac = generate_tac("int x = 10 + 20 * 3;")

        self.assertEqual(
            [str(instruction) for instruction in tac.instructions],
            [
                "t1 = 20 * 3",
                "t2 = 10 + t1",
                "x = t2",
            ],
        )
        self.assertEqual(tac.temp_count, 2)

    def test_multiple_statements_and_print(self):
        tac = generate_tac("int x = 1; x = x + 2; print(x);")

        self.assertEqual(
            [instruction.operation for instruction in tac.instructions],
            ["ASSIGN", "+", "ASSIGN", "PRINT"],
        )

    def test_if_and_while_generate_labels_and_branches(self):
        source = (
            "int x = 0;"
            "if (x < 10) { print(x); }"
            "while (x < 2) { x = x + 1; }"
        )
        tac = generate_tac(source)

        self.assertEqual(tac.label_count, 3)
        self.assertEqual(
            sum(instruction.operation == "LABEL" for instruction in tac.instructions),
            3,
        )
        self.assertGreaterEqual(
            sum(instruction.operation == "IF_FALSE" for instruction in tac.instructions),
            2,
        )
        self.assertTrue(
            any(instruction.operation == "GOTO" for instruction in tac.instructions)
        )

    def test_tac_statistics_use_program_counters_and_instructions(self):
        tac = generate_tac("int x = 1 + 2; print(x);")

        self.assertEqual(
            calculate_tac_statistics(tac),
            {
                "instruction_count": 3,
                "temporary_count": 1,
                "label_count": 0,
                "arithmetic_count": 1,
                "assignment_count": 1,
                "comparison_count": 0,
                "branch_count": 0,
                "jump_count": 0,
                "print_count": 1,
            },
        )

    def test_tac_api_preserves_fields_and_adds_statistics(self):
        response = app.test_client().post(
            "/api/tac",
            json={"source": "int x = 10 + 20 * 3; print(x);"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("instructions", data)
        self.assertIn("text", data)
        self.assertEqual(data["statistics"]["instruction_count"], 4)
        self.assertEqual(data["statistics"]["temporary_count"], 2)
        self.assertEqual(data["temporaries"], ["t1", "t2"])
        self.assertEqual(data["instructions"][0]["op"], "*")
        self.assertEqual(data["instructions"][0]["arg1"], "20")
        self.assertEqual(data["instructions"][0]["arg2"], "3")

    def test_tac_api_does_not_generate_semantically_invalid_program(self):
        response = app.test_client().post(
            "/api/tac",
            json={"source": "int x = y + 10;"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Semantic Error", data["error"])
        self.assertIn("Variable 'y' is not declared", data["error"])
        self.assertNotIn("instructions", data)


if __name__ == "__main__":
    unittest.main()
