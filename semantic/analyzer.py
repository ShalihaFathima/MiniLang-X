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
    pass


class SemanticAnalyzer:

    def __init__(self):
        self.symbol_table = SymbolTable()

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
            f"Unknown AST node: {type(node).__name__}"
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
            raise SemanticError(
                f"Variable '{node.name}' "
                f"already declared"
            )

        initialized = node.initializer is not None

        self.symbol_table.declare(
            name=node.name,
            data_type=node.data_type,
            initialized=initialized,
        )

        if node.initializer:

            expression_type = self.visit(
                node.initializer
            )

            if not self.types_compatible(
                node.data_type,
                expression_type
            ):
                raise SemanticError(
                    f"Cannot assign {expression_type} "
                    f"to {node.data_type} variable "
                    f"'{node.name}'"
                )

    def visit_assignment(self, node):

        symbol = self.symbol_table.lookup(
            node.name
        )

        if symbol is None:
            raise SemanticError(
                f"Variable '{node.name}' "
                f"is not declared"
            )

        expression_type = self.visit(
            node.expression
        )

        if not self.types_compatible(
            symbol.data_type,
            expression_type
        ):
            raise SemanticError(
                f"Cannot assign {expression_type} "
                f"to {symbol.data_type} variable "
                f"'{node.name}'"
            )

        symbol.initialized = True

    def visit_print(self, node):
        self.visit(node.expression)

    def visit_if(self, node):

        condition_type = self.visit(
            node.condition
        )

        if condition_type != "bool":
            raise SemanticError(
                "If condition must be boolean"
            )

        self.visit(node.then_branch)

        if node.else_branch:
            self.visit(node.else_branch)

    def visit_while(self, node):

        condition_type = self.visit(
            node.condition
        )

        if condition_type != "bool":
            raise SemanticError(
                "While condition must be boolean"
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
            raise SemanticError(
                f"Variable '{node.name}' "
                f"is not declared"
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
                raise SemanticError(
                    f"Operator '{node.operator}' "
                    f"cannot be used with {left_type}"
                )

            if right_type not in ("int", "float"):
                raise SemanticError(
                    f"Operator '{node.operator}' "
                    f"cannot be used with {right_type}"
                )

            if left_type == "float" or right_type == "float":
                return "float"

            return "int"

        if node.operator in comparison_operators:

            if not self.types_compatible(
                left_type,
                right_type
            ):
                raise SemanticError(
                    f"Cannot compare "
                    f"{left_type} and {right_type}"
                )

            return "bool"

        raise SemanticError(
            f"Unknown operator '{node.operator}'"
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
                raise SemanticError(
                    "Unary '-' requires "
                    "a numeric value"
                )

            return operand_type

        if node.operator == "!":

            if operand_type != "bool":
                raise SemanticError(
                    "Unary '!' requires "
                    "a boolean value"
                )

            return "bool"

        raise SemanticError(
            f"Unknown unary operator "
            f"'{node.operator}'"
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