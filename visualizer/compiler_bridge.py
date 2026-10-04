from lexer.lexer import Lexer
from lexer.statistics import calculate_token_statistics
from parser.parser import Parser
from ir.generator import TACGenerator
from ir.statistics import calculate_tac_statistics
from optimizer.cfg import ControlFlowGraph
from semantic.analyzer import SemanticAnalyzer
from semantic.analyzer import SemanticError
from semantic.statistics import calculate_semantic_statistics

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
from syntax_tree.statistics import calculate_ast_statistics


def tokenize_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    return tokens_to_data(tokens)


def tokenize_source_with_statistics(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    return (
        tokens_to_data(tokens),
        calculate_token_statistics(tokens, lexer.comment_count),
    )


def tokens_to_data(tokens):
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
    _, ast = _parse_source_ast(source)
    return ast_to_dict(ast)


def parse_source_with_statistics(source):
    tokens, ast = _parse_source_ast(source)
    statistics = calculate_ast_statistics(ast)
    statistics["token_count"] = len(tokens) - 1
    return ast_to_dict(ast), statistics


def _parse_source_ast(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens, source=source)
    ast = parser.parse()
    return tokens, ast


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

    parser = Parser(tokens, source=source)
    ast = parser.parse()

    analyzer = SemanticAnalyzer(
        node_locations=semantic_node_locations(ast, tokens),
        source=source,
    )

    try:
        analyzer.analyze(ast)
        return {
            "success": True,
            "valid": True,
            "symbols": semantic_symbols_to_dicts(analyzer.symbol_table),
            "statistics": calculate_semantic_statistics(
                ast,
                analyzer.symbol_table,
            ),
            "errors": [],
            "message": "Semantic analysis completed successfully.",
        }

    except SemanticError as error:
        error_data = {
            "type": error.error_type,
            "message": error.message,
            "line": error.line,
            "column": error.column,
            "source_context": error.source_context,
        }
        return {
            "success": True,
            "valid": False,
            "symbols": semantic_symbols_to_dicts(analyzer.symbol_table),
            "statistics": calculate_semantic_statistics(
                ast,
                analyzer.symbol_table,
                error_count=1,
            ),
            "errors": [error_data],
            "error_details": error_data,
            "error": str(error),
        }


def semantic_symbols_to_dicts(symbol_table):
    symbols = []
    for symbol in symbol_table.symbols:
        symbols.append({
            "name": symbol.name,
            "data_type": symbol.data_type,
            "scope_level": symbol.scope_level,
            "scope": (
                "global"
                if symbol.scope_level == 0
                else f"scope {symbol.scope_level}"
            ),
            "initialized": symbol.initialized,
            "line": symbol.line,
            "column": symbol.column,
        })
    return symbols


def semantic_node_locations(ast, tokens):
    identifier_nodes = []
    literal_nodes = []
    control_nodes = []

    def visit(node):
        if isinstance(node, Program):
            for statement in node.statements:
                visit(statement)
        elif isinstance(node, Block):
            for statement in node.statements:
                visit(statement)
        elif isinstance(node, VarDeclaration):
            identifier_nodes.append((node, node.name))
            if node.initializer is not None:
                visit(node.initializer)
        elif isinstance(node, Assignment):
            identifier_nodes.append((node, node.name))
            visit(node.expression)
        elif isinstance(node, PrintStatement):
            visit(node.expression)
        elif isinstance(node, IfStatement):
            control_nodes.append((node, "IF"))
            visit(node.condition)
            visit(node.then_branch)
            if node.else_branch is not None:
                visit(node.else_branch)
        elif isinstance(node, WhileStatement):
            control_nodes.append((node, "WHILE"))
            visit(node.condition)
            visit(node.body)
        elif isinstance(node, BinaryExpression):
            visit(node.left)
            visit(node.right)
        elif isinstance(node, UnaryExpression):
            visit(node.operand)
        elif isinstance(node, Identifier):
            identifier_nodes.append((node, node.name))
        elif isinstance(node, Literal):
            literal_nodes.append(node)
        else:
            raise TypeError(f"Unsupported AST node: {type(node).__name__}")

    visit(ast)
    identifier_tokens = [
        token for token in tokens
        if token.type.name == "IDENTIFIER"
    ]

    locations = {}
    if len(identifier_nodes) == len(identifier_tokens):
        if all(
            name == token.value
            for (node, name), token in zip(identifier_nodes, identifier_tokens)
        ):
            for (node, _), token in zip(identifier_nodes, identifier_tokens):
                locations[id(node)] = token

    literal_tokens = [
        token for token in tokens
        if token.type.name in {
            "INTEGER",
            "FLOAT_LITERAL",
            "STRING_LITERAL",
            "TRUE",
            "FALSE",
        }
    ]
    if len(literal_nodes) == len(literal_tokens):
        literal_locations = {}
        for node, token in zip(literal_nodes, literal_tokens):
            if node.data_type != {
                "INTEGER": "int",
                "FLOAT_LITERAL": "float",
                "STRING_LITERAL": "string",
                "TRUE": "bool",
                "FALSE": "bool",
            }[token.type.name]:
                break
            if str(node.value).lower() != token.value.lower():
                break
            literal_locations[id(node)] = token
        else:
            locations.update(literal_locations)

    used_tokens = {id(token) for token in locations.values()}
    for node, token_type in control_nodes:
        token = next(
            (
                candidate for candidate in tokens
                if candidate.type.name == token_type
                and id(candidate) not in used_tokens
            ),
            None,
        )
        if token is not None:
            locations[id(node)] = token
            used_tokens.add(id(token))

    return locations


def tac_source(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens, source=source)
    ast = parser.parse()

    from semantic.analyzer import SemanticError

    try:
        SemanticAnalyzer().analyze(ast)
    except SemanticError as error:
        raise StageError("Semantic Error", error) from error

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
        "temporaries": [
            f"t{index}"
            for index in range(1, tac.temp_count + 1)
        ],
        "labels": [
            instruction.result
            for instruction in tac.instructions
            if instruction.operation == "LABEL"
        ],
        "statistics": calculate_tac_statistics(tac),
    }


def cfg_source(source):
    from optimizer.cfg import ControlFlowGraph
    from optimizer.statistics import calculate_cfg_statistics
    from ir.generator import TACGenerator

    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens, source=source)
        ast = parser.parse()
    except SyntaxError as error:
        raise StageError("Syntax Error", error) from error

    try:
        SemanticAnalyzer().analyze(ast)
    except SemanticError as error:
        raise StageError("Semantic Error", error) from error

    generator = TACGenerator()
    tac = generator.generate(ast)

    cfg = ControlFlowGraph(tac.instructions)

    cfg_blocks = list(cfg.blocks)

    block_ids = {id(block): block.block_id for block in cfg_blocks}
    label_to_block = {
        instruction.result: block
        for block in cfg_blocks
        for instruction in block.instructions
        if instruction.operation == "LABEL"
    }

    blocks = []
    edges = []

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
                last = block.instructions[-1] if block.instructions else None
                edge_type = "fallthrough"

                if last and last.operation == "GOTO":
                    edge_type = "jump"
                elif last and last.operation in {"IF_FALSE", "IF_TRUE"}:
                    target = label_to_block.get(last.result)
                    next_block = (
                        cfg_blocks[index + 1]
                        if index + 1 < len(cfg_blocks)
                        else None
                    )
                    if target is next_block and target is successor:
                        edge_type = "true/false"
                    elif target is successor:
                        edge_type = (
                            "false"
                            if last.operation == "IF_FALSE"
                            else "true"
                        )
                    elif next_block is successor:
                        edge_type = (
                            "true"
                            if last.operation == "IF_FALSE"
                            else "false"
                        )

                edges.append({
                    "source": block.block_id,
                    "target": successor_id,
                    "type": edge_type,
                })

        blocks.append({
            "id": block.block_id,
            "instructions": instructions,
            "predecessors": predecessors,
            "successors": successors
        })

    return {
        "success": True,
        "blocks": blocks,
        "edges": edges,
        "statistics": calculate_cfg_statistics(cfg),
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
        ast = Parser(tokens, source=source).parse()
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
    from optimizer.statistics import compare_optimized_instructions

    _, tac, optimized_tac, _ = compile_to_optimized_tac(source)

    original = [str(i) for i in tac.instructions]
    optimized = [str(i) for i in optimized_tac.instructions]
    transformations, changed_indices, statistics = (
        compare_optimized_instructions(
            tac.instructions,
            optimized_tac.instructions,
        )
    )

    return {
        "success": True,
        "original": tac_instructions_to_dicts(tac.instructions),
        "optimized": tac_instructions_to_dicts(optimized_tac.instructions),
        "original_text": str(tac),
        "optimized_text": str(optimized_tac),
        "changed": original != optimized,
        "changed_indices": changed_indices,
        "statistics": statistics,
        "transformations": transformations,
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
    from backend.statistics import calculate_backend_statistics
    from backend.vm import VirtualMachine

    _, _, optimized_tac, variable_types = compile_to_optimized_tac(source)

    try:
        target_program = CodeGenerator(variable_types).generate(optimized_tac)
    except RuntimeError as error:
        raise StageError("Backend Generation Failed", error) from error

    vm = VirtualMachine(target_program)

    trace = []
    steps = 0
    output = io.StringIO()
    runtime_error = None
    execution_limit_reached = False
    trace_truncated = False

    with redirect_stdout(output):
        while vm.running and vm.pc < len(vm.instructions):
            if steps >= MAX_VM_STEPS:
                execution_limit_reached = True
                runtime_error = (
                    f"Maximum VM execution steps exceeded "
                    f"({MAX_VM_STEPS:,})"
                )
                break

            pc = vm.pc
            instruction = vm.instructions[pc]
            stack_before = [repr(value) for value in vm.stack]
            record_trace = len(trace) < MAX_TRACE_ENTRIES
            output_position = output.tell() if record_trace else None

            try:
                vm.execute(instruction)
            except RuntimeError as error:
                runtime_error = f"Runtime Error: {error}"
                if record_trace:
                    trace.append({
                        "step": steps + 1,
                        "pc": pc,
                        "instruction": str(instruction),
                        "stack": [repr(value) for value in vm.stack],
                        "stack_before": stack_before,
                        "memory": [
                            {"name": name, "value": repr(value)}
                            for name, value in vm.memory.items()
                        ],
                        "output": output.getvalue()[output_position:],
                        "error": runtime_error,
                    })
                else:
                    trace_truncated = True
                break

            steps += 1

            if record_trace:
                trace.append({
                    "step": steps,
                    "pc": pc,
                    "instruction": str(instruction),
                    "stack": [repr(value) for value in vm.stack],
                    "stack_before": stack_before,
                    "memory": [
                        {"name": name, "value": repr(value)}
                        for name, value in vm.memory.items()
                    ],
                    "output": output.getvalue()[output_position:],
                })
            else:
                trace_truncated = True

    status = (
        "execution_limit"
        if execution_limit_reached
        else "runtime_error"
        if runtime_error
        else "success"
    )

    return {
        "success": True,
        "instructions": [
            {
                "index": index,
                "text": str(instruction),
                "opcode": instruction.opcode,
                "operand1": instruction.operand1,
                "operand2": instruction.operand2,
            }
            for index, instruction in enumerate(target_program.instructions)
        ],
        "statistics": calculate_backend_statistics(target_program),
        "trace": trace,
        "trace_truncated": trace_truncated,
        "steps": steps,
        "output": output.getvalue(),
        "memory": [
            {"name": name, "value": repr(value)}
            for name, value in vm.memory.items()
        ],
        "stack": [repr(value) for value in vm.stack],
        "runtime_error": runtime_error,
        "status": status,
        "execution_limit_reached": execution_limit_reached,
    }
