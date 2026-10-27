from syntax_tree.nodes import (
    ASTNode,
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


def _children(node):
    if isinstance(node, (Program, Block)):
        return node.statements
    if isinstance(node, VarDeclaration):
        return [node.initializer] if node.initializer is not None else []
    if isinstance(node, Assignment):
        return [node.expression]
    if isinstance(node, PrintStatement):
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


def calculate_ast_statistics(root):
    counts = {
        "total_nodes": 0,
        "max_depth": 0,
        "statement_count": 0,
        "expression_count": 0,
        "identifier_count": 0,
        "literal_count": 0,
        "operator_count": 0,
    }

    def visit(node, depth):
        if not isinstance(node, ASTNode):
            raise TypeError(f"Expected ASTNode, got {type(node).__name__}")

        counts["total_nodes"] += 1
        counts["max_depth"] = max(counts["max_depth"], depth)
        counts["statement_count"] += isinstance(node, STATEMENT_TYPES)
        counts["expression_count"] += isinstance(node, EXPRESSION_TYPES)
        counts["identifier_count"] += isinstance(node, Identifier)
        counts["literal_count"] += isinstance(node, Literal)
        counts["operator_count"] += isinstance(
            node,
            (BinaryExpression, UnaryExpression),
        )

        for child in _children(node):
            visit(child, depth + 1)

    visit(root, 1)
    return counts
