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

from errors import format_error, source_context
from semantic.symbol_table import SymbolTable


class SemanticError(Exception):
    """
    A semantic error with a category and, when known, a location.

    error_type is one of: Undeclared Variable, Duplicate Declaration,
    Type Mismatch, Invalid Condition, Invalid Operation.

    Without a location, str(error) is just the message, e.g.
    "Variable 'y' is not declared".
    """

    def __init__(self, message, error_type="Semantic Error",
                 line=None, column=None, source=None):
        self.message = message
        self.error_type = error_type
        self.line = line
        self.column = column
        self.source_context = source_context(source, line, column)

        if line is None:
            text = message
        else:
            text = format_error(
                "Semantic Error",
                line,
                column,
                [f"{error_type}: {message}"],
                self.source_context,
            )

        super().__init__(text)


class SemanticAnalyzer:

    def __init__(self, node_locations=None, source=None):
        self.symbol_table = SymbolTable()

        # Optional map: id(AST node) -> token, used to report the
        # line/column of errors and declarations.
        self.node_locations = node_locations or {}
        self.source = source

    def location(self, node):
        """(line, column) of a node, or of its first located operand."""
        token = self.node_locations.get(id(node))

        if token is not None:
            return token.line, token.column

        for child in (
            getattr(node, "left", None),
            getattr(node, "right", None),
            getattr(node, "operand", None),
        ):
            if child is not None:
                line, column = self.location(child)
                if line is not None:
                    return line, column

        return None, None

    def error(self, error_type, message, node):
        line, column = self.location(node)
        return SemanticError(message, error_type, line, column, self.source)

    def analyze(self, program):
        self.visit(program)
        return self.symbol_table

    # -------------------------
    # Program
    # -------------------------

    def visit(self, node):

        if isinstance(node, Program):
            return self.visit_program(node)

        if isinstance(node, Block):
            return self.visit_block(node)

        if isinstance(node, VarDeclaration):
            return self.visit_declaration(node)

        if isinstance(node, Assignment):
            return self.visit_assignment(node)

        if isinstance(node, PrintStatement):
            return self.visit_print(node)

        if isinstance(node, IfStatement):
            return self.visit_if(node)

        if isinstance(node, WhileStatement):
            return self.visit_while(node)

        if isinstance(node, BinaryExpression):
            return self.visit_binary(node)

        if isinstance(node, UnaryExpression):
            return self.visit_unary(node)

        if isinstance(node, Literal):
            return node.data_type

        if isinstance(node, Identifier):
            return self.visit_identifier(node)

        raise SemanticError(
            f"Unknown AST node: {type(node).__name__}",
            "Invalid Operation",
        )

    # -------------------------
    # Statements
    # -------------------------

    def visit_program(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_block(self, node):
        self.symbol_table.enter_scope()

        try:
            for statement in node.statements:
                self.visit(statement)
        finally:
            self.symbol_table.exit_scope()

    def visit_declaration(self, node):

        if self.symbol_table.lookup_current_scope(node.name):
            raise self.error(
                "Duplicate Declaration",
                f"Variable '{node.name}' already declared",
                node,
            )

        initialized = node.initializer is not None
        line, column = self.location(node)

        self.symbol_table.declare(
            name=node.name,
            data_type=node.data_type,
            initialized=initialized,
            line=line,
            column=column,
        )

        if node.initializer:

            expression_type = self.visit(
                node.initializer
            )

            if not self.types_compatible(
                node.data_type,
                expression_type
            ):
                raise self.error(
                    "Type Mismatch",
                    f"Cannot assign {expression_type} "
                    f"to {node.data_type} variable "
                    f"'{node.name}'",
                    node,
                )

    def visit_assignment(self, node):

        symbol = self.symbol_table.lookup(
            node.name
        )

        if symbol is None:
            raise self.error(
                "Undeclared Variable",
                f"Variable '{node.name}' is not declared",
                node,
            )

        expression_type = self.visit(
            node.expression
        )

        if not self.types_compatible(
            symbol.data_type,
            expression_type
        ):
            raise self.error(
                "Type Mismatch",
                f"Cannot assign {expression_type} "
                f"to {symbol.data_type} variable "
                f"'{node.name}'",
                node,
            )

        symbol.initialized = True

    def visit_print(self, node):
        self.visit(node.expression)

    def visit_if(self, node):

        condition_type = self.visit(
            node.condition
        )

        if condition_type != "bool":
            raise self.error(
                "Invalid Condition",
                "If condition must be boolean",
                node,
            )

        self.visit(node.then_branch)

        if node.else_branch:
            self.visit(node.else_branch)

    def visit_while(self, node):

        condition_type = self.visit(
            node.condition
        )

        if condition_type != "bool":
            raise self.error(
                "Invalid Condition",
                "While condition must be boolean",
                node,
            )

        self.visit(node.body)

    # -------------------------
    # Expressions
    # -------------------------

    def visit_identifier(self, node):

        symbol = self.symbol_table.lookup(
            node.name
        )

        if symbol is None:
            raise self.error(
                "Undeclared Variable",
                f"Variable '{node.name}' is not declared",
                node,
            )

        return symbol.data_type

    def visit_binary(self, node):

        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        arithmetic_operators = {
            "+",
            "-",
            "*",
            "/",
        }

        comparison_operators = {
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
        }

        if node.operator in arithmetic_operators:

            if left_type not in ("int", "float"):
                raise self.error(
                    "Invalid Operation",
                    f"Operator '{node.operator}' "
                    f"cannot be used with {left_type}",
                    node,
                )

            if right_type not in ("int", "float"):
                raise self.error(
                    "Invalid Operation",
                    f"Operator '{node.operator}' "
                    f"cannot be used with {right_type}",
                    node,
                )

            if left_type == "float" or right_type == "float":
                return "float"

            return "int"

        if node.operator in comparison_operators:

            if not self.types_compatible(
                left_type,
                right_type
            ):
                raise self.error(
                    "Type Mismatch",
                    f"Cannot compare "
                    f"{left_type} and {right_type}",
                    node,
                )

            return "bool"

        raise self.error(
            "Invalid Operation",
            f"Unknown operator '{node.operator}'",
            node,
        )

    def visit_unary(self, node):

        operand_type = self.visit(
            node.operand
        )

        if node.operator == "-":

            if operand_type not in (
                "int",
                "float",
            ):
                raise self.error(
                    "Invalid Operation",
                    "Unary '-' requires a numeric value",
                    node,
                )

            return operand_type

        if node.operator == "!":

            if operand_type != "bool":
                raise self.error(
                    "Invalid Operation",
                    "Unary '!' requires a boolean value",
                    node,
                )

            return "bool"

        raise self.error(
            "Invalid Operation",
            f"Unknown unary operator '{node.operator}'",
            node,
        )

    # -------------------------
    # Type compatibility
    # -------------------------

    def types_compatible(
        self,
        expected,
        actual
    ):
        if expected == actual:
            return True

        # Allow int → float
        if expected == "float" and actual == "int":
            return True

        return False