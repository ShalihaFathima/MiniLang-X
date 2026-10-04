import unittest
from unittest.mock import patch

from backend.code_generator import CodeGenerator
from backend.instructions import TargetProgram
from backend.statistics import calculate_backend_statistics
from backend.vm import VirtualMachine
from ir.generator import TACGenerator
from lexer.lexer import Lexer
from optimizer.optimizer import collect_variable_types
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from visualizer.app import app
from visualizer.compiler_bridge import run_source
import visualizer.compiler_bridge as compiler_bridge


def compile_target(source):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens, source=source).parse()
    SemanticAnalyzer().analyze(ast)
    tac = TACGenerator().generate(ast)
    variable_types = collect_variable_types(ast)
    return CodeGenerator(variable_types).generate(tac)


class BackendVMTests(unittest.TestCase):
    def test_target_generation_uses_existing_stack_instruction_model(self):
        target = compile_target("int x = 4 + 5; print(x);")

        self.assertEqual(
            [instruction.opcode for instruction in target.instructions],
            [
                "PUSH",
                "PUSH",
                "ADD",
                "STORE",
                "LOAD",
                "STORE",
                "LOAD",
                "PRINT",
                "HALT",
            ],
        )
        self.assertEqual(target.instructions[3].operand1, "t1")
        self.assertEqual(target.instructions[3].operand2, None)

    def test_backend_statistics_count_actual_opcodes(self):
        target = TargetProgram()
        target.emit("PUSH", 4)
        target.emit("STORE", "x")
        target.emit("LOAD", "x")
        target.emit("ADD")
        target.emit("CMP_EQ")
        target.emit("JMP_IF_FALSE", "L1")
        target.emit("PRINT")
        target.emit("LABEL", "L1")
        target.emit("HALT")

        self.assertEqual(
            calculate_backend_statistics(target),
            {
                "target_instruction_count": 9,
                "label_count": 1,
                "load_count": 1,
                "push_count": 1,
                "store_count": 1,
                "memory_operation_count": 2,
                "arithmetic_count": 1,
                "comparison_count": 1,
                "jump_count": 1,
                "conditional_branch_count": 1,
                "print_count": 1,
                "halt_count": 1,
            },
        )

    def test_vm_executes_arithmetic_assignment_and_print(self):
        result = run_source("int x = 10 + 20 * 3; print(x);")

        self.assertEqual(result["output"], "70\n")
        self.assertIsNone(result["runtime_error"])
        self.assertEqual(result["status"], "success")
        self.assertIn({"name": "x", "value": "70"}, result["memory"])
        self.assertEqual(result["stack"], [])

    def test_execution_trace_contains_real_stack_memory_and_output(self):
        result = run_source("int x = 4; print(x);")
        print_step = next(
            entry
            for entry in result["trace"]
            if entry["instruction"] == "PRINT"
        )

        self.assertEqual(print_step["stack_before"], ["4"])
        self.assertEqual(print_step["stack"], [])
        self.assertEqual(print_step["memory"], [{"name": "x", "value": "4"}])
        self.assertEqual(print_step["output"], "4\n")
        self.assertEqual(print_step["pc"], 3)
        self.assertIn("statistics", result)

    def test_conditional_execution_and_target_jumps(self):
        result = run_source(
            "int x = 0; if (x == 0) { print(7); } else { print(9); }"
        )

        self.assertEqual(result["output"], "7\n")
        self.assertEqual(result["status"], "success")
        self.assertTrue(any(
            instruction["opcode"] == "JMP_IF_FALSE"
            for instruction in result["instructions"]
        ))
        self.assertTrue(any(
            instruction["opcode"] == "JMP"
            for instruction in result["instructions"]
        ))

    def test_run_api_preserves_existing_response_and_adds_details(self):
        response = app.test_client().post(
            "/api/run",
            json={"source": "int x = 6; print(x);"},
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertTrue(result["success"])
        for field in (
            "instructions",
            "trace",
            "trace_truncated",
            "steps",
            "output",
            "memory",
            "runtime_error",
        ):
            self.assertIn(field, result)
        self.assertIn("statistics", result)
        self.assertIn("stack", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["instructions"][0]["opcode"], "PUSH")
        self.assertIn("operand1", result["instructions"][0])

    def test_runtime_division_error_is_reported_without_traceback(self):
        result = run_source("int x = 1 / 0; print(x);")

        self.assertEqual(result["status"], "runtime_error")
        self.assertIn("Division by zero", result["runtime_error"])
        self.assertEqual(result["trace"][-1]["error"], result["runtime_error"])

        response = app.test_client().post(
            "/api/run",
            json={"source": "int x = 1 / 0; print(x);"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "runtime_error")

    def test_execution_step_limit_is_reported_and_stops_vm(self):
        with patch.object(compiler_bridge, "MAX_VM_STEPS", 12):
            result = run_source("int x = 0; while (true) { x = x + 1; }")

        self.assertEqual(result["status"], "execution_limit")
        self.assertTrue(result["execution_limit_reached"])
        self.assertEqual(result["steps"], 12)
        self.assertIn("Maximum VM execution steps exceeded", result["runtime_error"])

    def test_execution_trace_limit_truncates_recording(self):
        with patch.object(compiler_bridge, "MAX_TRACE_ENTRIES", 2):
            result = run_source("int x = 4; print(x);")

        self.assertEqual(result["steps"], 5)
        self.assertEqual(len(result["trace"]), 2)
        self.assertTrue(result["trace_truncated"])

    def test_invalid_semantics_do_not_generate_or_execute_backend_code(self):
        response = app.test_client().post(
            "/api/run",
            json={"source": "int x = y + 10; print(x);"},
        )

        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertFalse(result["success"])
        self.assertIn("Semantic Error", result["error"])
        self.assertNotIn("instructions", result)
        self.assertNotIn("Traceback", result["error"])

    def test_optimized_execution_matches_original_valid_program_output(self):
        source = (
            "int x = 0;"
            "while (x < 4) { x = x + 1; }"
            "if (x == 4) { print(x); } else { print(0); }"
        )
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens, source=source).parse()
        SemanticAnalyzer().analyze(ast)
        variable_types = collect_variable_types(ast)
        original_tac = TACGenerator().generate(ast)
        original_target = CodeGenerator(variable_types).generate(original_tac)
        original_vm = VirtualMachine(original_target)

        import io
        from contextlib import redirect_stdout

        original_output = io.StringIO()
        with redirect_stdout(original_output):
            original_vm.run()

        optimized_result = run_source(source)

        self.assertEqual(optimized_result["output"], original_output.getvalue())
        self.assertEqual(optimized_result["output"], "4\n")
        self.assertEqual(optimized_result["status"], "success")


if __name__ == "__main__":
    unittest.main()
