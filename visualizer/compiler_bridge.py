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
            "op": getattr(instruction, "op", ""),
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

