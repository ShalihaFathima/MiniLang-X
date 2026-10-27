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


def calculate_semantic_statistics(
    program,
    symbol_table,
    error_count=0,
):
    statistics = {
        "symbol_count": len(symbol_table.symbols),
        "declaration_count": 0,
        "identifier_use_count": 0,
        "scope_count": symbol_table.scope_count,
        "error_count": error_count,
        "initialized_count": sum(
            symbol.initialized for symbol in symbol_table.symbols
        ),
        "variables_by_type": {},
    }

    for symbol in symbol_table.symbols:
        data_type = symbol.data_type
        statistics["variables_by_type"][data_type] = (
            statistics["variables_by_type"].get(data_type, 0) + 1
        )

    def visit(node):
        if isinstance(node, (Program, Block)):
            for statement in node.statements:
                visit(statement)
        elif isinstance(node, VarDeclaration):
            statistics["declaration_count"] += 1
            if node.initializer is not None:
                visit(node.initializer)
        elif isinstance(node, Assignment):
            visit(node.expression)
        elif isinstance(node, PrintStatement):
            visit(node.expression)
        elif isinstance(node, IfStatement):
            visit(node.condition)
            visit(node.then_branch)
            if node.else_branch is not None:
                visit(node.else_branch)
        elif isinstance(node, WhileStatement):
            visit(node.condition)
            visit(node.body)
        elif isinstance(node, BinaryExpression):
            visit(node.left)
            visit(node.right)
        elif isinstance(node, UnaryExpression):
            visit(node.operand)
        elif isinstance(node, Identifier):
            statistics["identifier_use_count"] += 1
        elif not isinstance(node, Literal):
            raise TypeError(f"Unsupported AST node: {type(node).__name__}")

    visit(program)
    return statistics
