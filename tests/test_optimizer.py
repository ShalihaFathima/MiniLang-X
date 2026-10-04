import io
import unittest
from contextlib import redirect_stdout

from backend.code_generator import CodeGenerator
from backend.vm import VirtualMachine
from ir.generator import TACGenerator
from ir.tac import TACInstruction
from lexer.lexer import Lexer
from optimizer.optimizer import Optimizer, collect_variable_types
from optimizer.statistics import compare_optimized_instructions
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from visualizer.app import app
from visualizer.compiler_bridge import optimize_source, run_source


def compile_original_tac(source):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens, source=source).parse()
    SemanticAnalyzer().analyze(ast)
    return ast, TACGenerator().generate(ast)


class OptimizerTests(unittest.TestCase):
    def test_existing_constant_optimization_is_reported(self):
        result = optimize_source(
            "int x = 10 + 20 * 3; print(x);"
        )

        self.assertTrue(result["changed"])
        self.assertIn("t1 = 20 * 3", result["original_text"])
        self.assertIn("t1 = 60", result["optimized_text"])
        self.assertIn("x = 70", result["optimized_text"])
        self.assertTrue(result["transformations"])
        self.assertEqual(
            result["statistics"]["transformation_count"],
            len(result["transformations"]),
        )

    def test_arithmetic_identity_simplification_is_retained(self):
        optimized = Optimizer().algebraic_simplification([
            TACInstruction("+", arg1="x", arg2="0", result="t1"),
        ])

        self.assertEqual(len(optimized), 1)
        self.assertEqual(str(optimized[0]), "t1 = x")

    def test_optimization_diff_does_not_map_shifted_instructions_by_index(self):
        original = [
            TACInstruction("ASSIGN", arg1="1", result="a"),
            TACInstruction("ASSIGN", arg1="2", result="b"),
            TACInstruction("PRINT", arg1="b"),
        ]
        optimized = [
            TACInstruction("ASSIGN", arg1="3", result="b"),
            TACInstruction("PRINT", arg1="b"),
        ]

        transformations, changed_indices, statistics = (
            compare_optimized_instructions(original, optimized)
        )

        self.assertEqual(changed_indices, [])
        self.assertEqual(statistics["instructions_removed"], 1)
        self.assertEqual(statistics["optimization_percentage"], 33.3)
        self.assertEqual(transformations[0]["kind"], "changed")
        self.assertEqual(
            transformations[0]["before"],
            ["a = 1", "b = 2"],
        )
        self.assertEqual(transformations[0]["after"], ["b = 3"])

    def test_optimizer_api_preserves_fields_and_adds_statistics(self):
        response = app.test_client().post(
            "/api/optimize",
            json={"source": "int x = 10 + 20 * 3; print(x);"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        for field in (
            "original",
            "optimized",
            "original_text",
            "optimized_text",
            "changed",
            "changed_indices",
        ):
            self.assertIn(field, data)
        self.assertEqual(
            data["statistics"]["original_instruction_count"],
            len(data["original"]),
        )
        self.assertEqual(
            data["statistics"]["optimized_instruction_count"],
            len(data["optimized"]),
        )
        self.assertIn("transformations", data)

    def test_optimized_execution_matches_original_tac(self):
        source = "int x = 10 + 20 * 3; print(x);"
        ast, original_tac = compile_original_tac(source)
        variable_types = collect_variable_types(ast)
        original_output = io.StringIO()
        with redirect_stdout(original_output):
            VirtualMachine(
                CodeGenerator(variable_types).generate(original_tac)
            ).run()

        optimized_result = run_source(source)

        self.assertIsNone(optimized_result["runtime_error"])
        self.assertEqual(optimized_result["output"], original_output.getvalue())
        self.assertEqual(optimized_result["output"].strip(), "70")

    def test_conditional_optimized_execution_matches_original_tac(self):
        source = (
            "int x = 0;"
            "while (x < 4) { x = x + 1; }"
            "if (x == 4) { print(x); } else { print(0); }"
        )
        ast, original_tac = compile_original_tac(source)
        variable_types = collect_variable_types(ast)
        original_output = io.StringIO()
        with redirect_stdout(original_output):
            VirtualMachine(
                CodeGenerator(variable_types).generate(original_tac)
            ).run()

        optimized_result = run_source(source)

        self.assertIsNone(optimized_result["runtime_error"])
        self.assertEqual(optimized_result["output"], original_output.getvalue())
        self.assertEqual(optimized_result["output"].strip(), "4")

        api_result = app.test_client().post(
            "/api/optimize",
            json={"source": source},
        )
        self.assertEqual(api_result.status_code, 200)
        self.assertTrue(api_result.get_json()["success"])

    def test_optimizer_api_rejects_semantically_invalid_program(self):
        response = app.test_client().post(
            "/api/optimize",
            json={"source": "int x = missing;"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Semantic Error", data["error"])
        self.assertNotIn("Traceback", data["error"])


if __name__ == "__main__":
    unittest.main()
