from lexer.lexer import Lexer
from parser.parser import Parser
from ir.generator import TACGenerator
from optimizer.cfg import ControlFlowGraph
from semantic.analyzer import SemanticAnalyzer

from syntax_tree.nodes import (
    Program,
    Block,
    VarDeclaration,
    Assignment,
    PrintStatement,
    IfStatement,
    WhileStatement,
    BinaryExpression,
    UnaryExpression,
    Literal,
    Identifier,
)


def tokenize_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    return [
        {
            "type": token.type.name,
            "value": token.value,
            "line": token.line,
            "column": token.column,
        }
        for token in tokens
    ]


def parse_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    return ast_to_dict(ast)


def ast_to_dict(node):
    if isinstance(node, Program):
        return {
            "type": "Program",
            "children": [
                ast_to_dict(statement)
                for statement in node.statements
            ],
        }

    if isinstance(node, Block):
        return {
            "type": "Block",
            "children": [
                ast_to_dict(statement)
                for statement in node.statements
            ],
        }

    if isinstance(node, VarDeclaration):
        children = []

        if node.initializer is not None:
            children.append(ast_to_dict(node.initializer))

        return {
            "type": "VarDeclaration",
            "label": f"{node.name} : {node.data_type}",
            "name": node.name,
            "data_type": node.data_type,
            "children": children,
        }

    if isinstance(node, Assignment):
        return {
            "type": "Assignment",
            "label": node.name,
            "name": node.name,
            "children": [
                ast_to_dict(node.expression)
            ],
        }

    if isinstance(node, PrintStatement):
        return {
            "type": "PrintStatement",
            "children": [
                ast_to_dict(node.expression)
            ],
        }

    if isinstance(node, IfStatement):
        children = [
            ast_to_dict(node.condition),
            ast_to_dict(node.then_branch),
        ]

        if node.else_branch is not None:
            children.append(
                ast_to_dict(node.else_branch)
            )

        return {
            "type": "IfStatement",
            "children": children,
        }

    if isinstance(node, WhileStatement):
        return {
            "type": "WhileStatement",
            "children": [
                ast_to_dict(node.condition),
                ast_to_dict(node.body),
            ],
        }

    if isinstance(node, BinaryExpression):
        return {
            "type": "BinaryExpression",
            "operator": node.operator,
            "label": node.operator,
            "children": [
                ast_to_dict(node.left),
                ast_to_dict(node.right),
            ],
        }

    if isinstance(node, UnaryExpression):
        return {
            "type": "UnaryExpression",
            "operator": node.operator,
            "label": node.operator,
            "children": [
                ast_to_dict(node.operand),
            ],
        }

    if isinstance(node, Literal):
        return {
            "type": "Literal",
            "value": node.value,
            "data_type": node.data_type,
            "label": str(node.value),
            "children": [],
        }

    if isinstance(node, Identifier):
        return {
            "type": "Identifier",
            "name": node.name,
            "label": node.name,
            "children": [],
        }

    raise TypeError(
        f"Unsupported AST node: {type(node).__name__}"
    )


def semantic_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    analyzer = SemanticAnalyzer()

    try:
        analyzer.analyze(ast)

        symbols = []

        for level, scope in enumerate(
            analyzer.symbol_table.scopes
        ):
            for symbol in scope.values():
                symbols.append({
                    "name": symbol.name,
                    "data_type": symbol.data_type,
                    "scope_level": symbol.scope_level,
                    "initialized": symbol.initialized,
                })

        return {
            "success": True,
            "valid": True,
            "symbols": symbols,
            "message": "Semantic analysis completed successfully."
        }

    except Exception as error:

        symbols = []

        for level, scope in enumerate(
            analyzer.symbol_table.scopes
        ):
            for symbol in scope.values():
                symbols.append({
                    "name": symbol.name,
                    "data_type": symbol.data_type,
                    "scope_level": symbol.scope_level,
                    "initialized": symbol.initialized,
                })

        return {
            "success": True,
            "valid": False,
            "symbols": symbols,
            "error": str(error),
        }


def tac_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    generator = TACGenerator()
    tac = generator.generate(ast)

    instructions = []

    for instruction in tac.instructions:
        instructions.append({
            "op": instruction.operation,
            "arg1": getattr(instruction, "arg1", None),
            "arg2": getattr(instruction, "arg2", None),
            "result": getattr(instruction, "result", None),
            "label": getattr(instruction, "label", None),
        })

    return {
        "success": True,
        "instructions": instructions,
        "text": str(tac),
    }


def cfg_source(source):
    from optimizer.cfg import ControlFlowGraph
    from ir.generator import TACGenerator

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    generator = TACGenerator()
    tac = generator.generate(ast)

    cfg = ControlFlowGraph(tac.instructions)

    # BasicBlock does not expose an .id attribute.
    # Assign stable visual IDs based on their position.
    cfg_blocks = list(cfg.blocks)

    block_ids = {
        id(block): index
        for index, block in enumerate(cfg_blocks)
    }

    blocks = []

    for index, block in enumerate(cfg_blocks):

        instructions = []

        for instruction in block.instructions:
            instructions.append(str(instruction))

        predecessors = []

        for predecessor in block.predecessors:
            predecessor_id = block_ids.get(id(predecessor))

            if predecessor_id is not None:
                predecessors.append(predecessor_id)

        successors = []

        for successor in block.successors:
            successor_id = block_ids.get(id(successor))

            if successor_id is not None:
                successors.append(successor_id)

        blocks.append({
            "id": index,
            "instructions": instructions,
            "predecessors": predecessors,
            "successors": successors
        })

    return {
        "success": True,
        "blocks": blocks,
        "text": str(cfg)
    }



# =========================================================
# Optimizer, VM and Output stages
# =========================================================

# The dashboard steps the VM itself, so it can stop a program that
# never terminates instead of hanging the web server.
MAX_VM_STEPS = 100_000

# Only the first steps of the execution trace are sent to the page.
MAX_TRACE_ENTRIES = 300


class StageError(Exception):
    """A compiler error tagged with the phase that reported it."""

    def __init__(self, phase, error):
        super().__init__(f"{phase}: {error}")


def tac_instructions_to_dicts(instructions):
    return [
        {
            "op": instruction.operation,
            "arg1": instruction.arg1,
            "arg2": instruction.arg2,
            "result": instruction.result,
            "text": str(instruction),
        }
        for instruction in instructions
    ]


def compile_to_optimized_tac(source):
    """
    Run the same front end and optimizer as main.py.
    Returns (ast, tac, optimized_tac, variable_types).
    """
    from semantic.analyzer import SemanticError
    from optimizer.optimizer import Optimizer, collect_variable_types

    try:
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
    except SyntaxError as error:
        raise StageError("Syntax Error", error)

    try:
        SemanticAnalyzer().analyze(ast)
    except SemanticError as error:
        raise StageError("Semantic Error", error)

    tac = TACGenerator().generate(ast)

    variable_types = collect_variable_types(ast)
    optimized_tac = Optimizer(variable_types).optimize(tac)

    return ast, tac, optimized_tac, variable_types


def optimize_source(source):
    _, tac, optimized_tac, _ = compile_to_optimized_tac(source)

    original = [str(i) for i in tac.instructions]
    optimized = [str(i) for i in optimized_tac.instructions]

    return {
        "success": True,
        "original": tac_instructions_to_dicts(tac.instructions),
        "optimized": tac_instructions_to_dicts(optimized_tac.instructions),
        "original_text": str(tac),
        "optimized_text": str(optimized_tac),
        "changed": original != optimized,
        # Instruction positions whose text changed
        "changed_indices": [
            index
            for index, text in enumerate(optimized)
            if index >= len(original) or original[index] != text
        ],
    }


def run_source(source):
    """
    Generate target code from the optimized TAC and execute it on the
    existing VirtualMachine, one instruction at a time via its own
    execute() method, recording a trace and capturing printed output.
    """
    import io
    from contextlib import redirect_stdout

    from backend.code_generator import CodeGenerator
    from backend.vm import VirtualMachine

    _, _, optimized_tac, variable_types = compile_to_optimized_tac(source)

    target_program = CodeGenerator(variable_types).generate(optimized_tac)

    vm = VirtualMachine(target_program)

    trace = []
    steps = 0
    output = io.StringIO()
    runtime_error = None

    with redirect_stdout(output):
        try:
            while vm.running and vm.pc < len(vm.instructions):

                if steps >= MAX_VM_STEPS:
                    raise RuntimeError(
                        f"Execution stopped after {MAX_VM_STEPS:,} "
                        f"instructions (possible infinite loop)"
                    )

                pc = vm.pc
                instruction = vm.instructions[pc]

                vm.execute(instruction)
                steps += 1

                if len(trace) < MAX_TRACE_ENTRIES:
                    trace.append({
                        "step": steps,
                        "pc": pc,
                        "instruction": str(instruction),
                        "stack": [repr(value) for value in vm.stack],
                    })

        except RuntimeError as error:
            runtime_error = f"Runtime Error: {error}"

    return {
        "success": True,
        "instructions": [
            {"index": index, "text": str(instruction), "opcode": instruction.opcode}
            for index, instruction in enumerate(target_program.instructions)
        ],
        "trace": trace,
        "trace_truncated": steps > len(trace),
        "steps": steps,
        "output": output.getvalue(),
        "memory": [
            {"name": name, "value": repr(value)}
            for name, value in vm.memory.items()
        ],
        "runtime_error": runtime_error,
    }
