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

from semantic.symbol_table import SymbolTable


class SemanticError(Exception):
    def __init__(
        self,
        message,
        error_type="Semantic Error",
        line=None,
        column=None,
        source_context=None,
    ):
        self.message = message
        self.error_type = error_type
        self.line = line
        self.column = column
        self.source_context = source_context
        super().__init__(message)


class SemanticAnalyzer:

    def __init__(self, node_locations=None, source=None):
        self.symbol_table = SymbolTable()
        self.node_locations = node_locations or {}
        self.source = source

    def semantic_error(self, message, error_type, node=None):
        token = self.node_locations.get(id(node)) if node is not None else None
        source_context = None

        if token is not None and self.source is not None:
            lines = self.source.split("\n")
            if 1 <= token.line <= len(lines):
                source_line = lines[token.line - 1].rstrip("\r")
                prefix = source_line[:max(token.column - 1, 0)]
                source_context = (
                    f"{source_line.expandtabs(4)}\n"
                    f"{' ' * len(prefix.expandtabs(4))}^"
                )

        raise SemanticError(
            message,
            error_type=error_type,
            line=token.line if token is not None else None,
            column=token.column if token is not None else None,
            source_context=source_context,
        )

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
            error_type="Unsupported AST Node",
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
            self.semantic_error(
                f"Variable '{node.name}' "
                f"already declared",
                "Duplicate Declaration",
                node,
            )

        self.symbol_table.declare(
            name=node.name,
            data_type=node.data_type,
            line=getattr(self.node_locations.get(id(node)), "line", None),
            column=getattr(self.node_locations.get(id(node)), "column", None),
        )

        if node.initializer:

            expression_type = self.visit(
                node.initializer
            )

            if not self.types_compatible(
                node.data_type,
                expression_type
            ):
                self.semantic_error(
                    f"Cannot assign {expression_type} "
                    f"to {node.data_type} variable "
                    f"'{node.name}'",
                    "Type Mismatch",
                    node,
                )
            self.symbol_table.lookup_current_scope(node.name).initialized = True

    def visit_assignment(self, node):

        symbol = self.symbol_table.lookup(
            node.name
        )

        if symbol is None:
            self.semantic_error(
                f"Variable '{node.name}' "
                f"is not declared",
                "Undeclared Variable",
                node,
            )

        expression_type = self.visit(
            node.expression
        )

        if not self.types_compatible(
            symbol.data_type,
            expression_type
        ):
            self.semantic_error(
                f"Cannot assign {expression_type} "
                f"to {symbol.data_type} variable "
                f"'{node.name}'",
                "Type Mismatch",
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
            self.semantic_error(
                "If condition must be boolean",
                "Invalid Condition",
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
            self.semantic_error(
                "While condition must be boolean",
                "Invalid Condition",
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
            self.semantic_error(
                f"Variable '{node.name}' "
                f"is not declared",
                "Undeclared Variable",
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
                self.semantic_error(
                    f"Operator '{node.operator}' "
                    f"cannot be used with {left_type}",
                    "Invalid Operand Type",
                    node.left,
                )

            if right_type not in ("int", "float"):
                self.semantic_error(
                    f"Operator '{node.operator}' "
                    f"cannot be used with {right_type}",
                    "Invalid Operand Type",
                    node.right,
                )

            if left_type == "float" or right_type == "float":
                return "float"

            return "int"

        if node.operator in comparison_operators:

            if not self.types_compatible(
                left_type,
                right_type
            ):
                self.semantic_error(
                    f"Cannot compare "
                    f"{left_type} and {right_type}",
                    "Type Mismatch",
                    node.left,
                )

            return "bool"

        self.semantic_error(
            f"Unknown operator '{node.operator}'",
            "Invalid Operator",
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
                self.semantic_error(
                    "Unary '-' requires "
                    "a numeric value",
                    "Invalid Operand Type",
                    node.operand,
                )

            return operand_type

        if node.operator == "!":

            if operand_type != "bool":
                self.semantic_error(
                    "Unary '!' requires "
                    "a boolean value",
                    "Invalid Operand Type",
                    node.operand,
                )

            return "bool"

        self.semantic_error(
            f"Unknown unary operator "
            f"'{node.operator}'",
            "Invalid Operator",
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

        numeric_types = {"int", "float"}
        if expected in numeric_types and actual in numeric_types:
            return True

        return False