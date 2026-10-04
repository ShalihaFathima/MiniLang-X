import unittest

from ir.generator import TACGenerator
from lexer.lexer import Lexer
from optimizer.cfg import ControlFlowGraph
from optimizer.statistics import calculate_cfg_statistics
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from visualizer.app import app
from visualizer.compiler_bridge import cfg_source


def generate_cfg(source):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens, source=source).parse()
    SemanticAnalyzer().analyze(ast)
    tac = TACGenerator().generate(ast)
    return ControlFlowGraph(tac.instructions)


class CFGTests(unittest.TestCase):
    def test_sequential_program_forms_one_basic_block(self):
        cfg = generate_cfg("int x = 1; print(x);")

        self.assertEqual(len(cfg.blocks), 1)
        self.assertEqual(len(cfg.blocks[0].instructions), 2)
        self.assertEqual(cfg.blocks[0].successors, [])

    def test_arithmetic_program_instructions_are_retained(self):
        cfg = generate_cfg("int x = 10 + 20 * 3; print(x);")

        self.assertEqual(
            [str(instruction) for instruction in cfg.blocks[0].instructions],
            [
                "t1 = 20 * 3",
                "t2 = 10 + t1",
                "x = t2",
                "print x",
            ],
        )

    def test_conditional_cfg_has_real_branch_edges(self):
        result = cfg_source(
            "int x = 0; if (x < 2) { print(x); }"
        )

        self.assertTrue(any(edge["type"] == "true" for edge in result["edges"]))
        self.assertTrue(any(edge["type"] == "false" for edge in result["edges"]))
        self.assertTrue(any(block["predecessors"] for block in result["blocks"]))
        self.assertTrue(any(block["successors"] for block in result["blocks"]))

    def test_loop_cfg_has_back_edge_and_label_blocks(self):
        result = cfg_source(
            "int x = 0; while (x < 3) { x = x + 1; }"
        )

        block_ids = {block["id"] for block in result["blocks"]}
        self.assertTrue(any(
            edge["target"] <= edge["source"]
            for edge in result["edges"]
        ))
        self.assertTrue(any(
            instruction.endswith(":")
            for block in result["blocks"]
            for instruction in block["instructions"]
        ))
        self.assertEqual(result["statistics"]["block_count"], len(block_ids))

    def test_cfg_statistics_count_real_blocks_and_edges(self):
        cfg = generate_cfg(
            "int x = 0; if (x < 1) { print(x); }"
        )

        statistics = calculate_cfg_statistics(cfg)

        self.assertEqual(statistics["block_count"], len(cfg.blocks))
        self.assertEqual(
            statistics["edge_count"],
            sum(len(block.successors) for block in cfg.blocks),
        )
        self.assertEqual(statistics["entry_block_count"], 1)
        self.assertEqual(statistics["conditional_branch_count"], 1)
        self.assertGreaterEqual(statistics["maximum_block_size"], 1)

    def test_cfg_api_preserves_fields_and_adds_edges_and_statistics(self):
        response = app.test_client().post(
            "/api/cfg",
            json={"source": "int x = 0; if (x < 2) { print(x); }"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("blocks", data)
        self.assertIn("text", data)
        self.assertIn("edges", data)
        self.assertIn("statistics", data)
        self.assertEqual(
            data["statistics"]["edge_count"],
            len(data["edges"]),
        )

    def test_cfg_api_rejects_semantically_invalid_program(self):
        response = app.test_client().post(
            "/api/cfg",
            json={"source": "int x = missing;"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Semantic Error", data["error"])
        self.assertIn("missing", data["error"])
        self.assertNotIn("Traceback", data["error"])


if __name__ == "__main__":
    unittest.main()
