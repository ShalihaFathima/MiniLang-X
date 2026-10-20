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


STATEMENT_TYPES = (
    VarDeclaration,
    Assignment,
    PrintStatement,
    IfStatement,
    WhileStatement,
)

EXPRESSION_TYPES = (
    BinaryExpression,
    UnaryExpression,
    Literal,
    Identifier,
)


def ast_children(node):
    """Child nodes of an AST node, in source order."""
    if isinstance(node, (Program, Block)):
        return list(node.statements)

    if isinstance(node, VarDeclaration):
        return [node.initializer] if node.initializer is not None else []

    if isinstance(node, (Assignment, PrintStatement)):
        return [node.expression]

    if isinstance(node, IfStatement):
        children = [node.condition, node.then_branch]
        if node.else_branch is not None:
            children.append(node.else_branch)
        return children

    if isinstance(node, WhileStatement):
        return [node.condition, node.body]

    if isinstance(node, BinaryExpression):
        return [node.left, node.right]

    if isinstance(node, UnaryExpression):
        return [node.operand]

    if isinstance(node, (Literal, Identifier)):
        return []

    raise TypeError(f"Unsupported AST node: {type(node).__name__}")


def calculate_ast_statistics(ast):
    """
    Count the nodes of an AST. Depth counts the root as level 1.
    Statements are declarations, assignments, print, if and while;
    expressions are operators, literals and identifier uses.
    """
    nodes = []
    max_depth = 0

    stack = [(ast, 1)]

    while stack:
        node, depth = stack.pop()
        nodes.append(node)
        max_depth = max(max_depth, depth)

        for child in ast_children(node):
            stack.append((child, depth + 1))

    def count(types):
        return sum(isinstance(node, types) for node in nodes)

    return {
        "total_nodes": len(nodes),
        "max_depth": max_depth,
        "statement_count": count(STATEMENT_TYPES),
        "expression_count": count(EXPRESSION_TYPES),
        "identifier_count": count(Identifier),
        "literal_count": count(Literal),
        "operator_count": count((BinaryExpression, UnaryExpression)),
    }
