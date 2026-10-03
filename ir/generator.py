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

from ir.tac import TACProgram


class TACGenerator:
    """
    Converts the MiniLang-X AST into
    Three Address Code.
    """

    def __init__(self):
        self.tac = TACProgram()

    # -------------------------
    # Entry point
    # -------------------------

    def generate(self, program):
        self.visit(program)
        return self.tac

    # -------------------------
    # Generic visitor
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
            return self.visit_literal(node)

        if isinstance(node, Identifier):
            return self.visit_identifier(node)

        raise RuntimeError(
            f"Unknown AST node: "
            f"{type(node).__name__}"
        )

    # -------------------------
    # Program
    # -------------------------

    def visit_program(self, node):

        for statement in node.statements:
            self.visit(statement)

    # -------------------------
    # Block
    # -------------------------

    def visit_block(self, node):

        for statement in node.statements:
            self.visit(statement)

    # -------------------------
    # Variable declaration
    # -------------------------

    def visit_declaration(self, node):

        # Declaration without initializer:

        # int x;

        if node.initializer is None:
            return

        # Declaration with initializer:

        # int x = 10;

        value = self.visit(
            node.initializer
        )

        self.tac.emit(
            "ASSIGN",
            arg1=value,
            result=node.name,
        )

    # -------------------------
    # Assignment
    # -------------------------

    def visit_assignment(self, node):

        # Example:
        #
        # x = y + 10;

        value = self.visit(
            node.expression
        )

        self.tac.emit(
            "ASSIGN",
            arg1=value,
            result=node.name,
        )

    # -------------------------
    # Print
    # -------------------------

    def visit_print(self, node):

        # Example:
        #
        # print(x);

        value = self.visit(
            node.expression
        )

        self.tac.emit(
            "PRINT",
            arg1=value,
        )

    # -------------------------
    # If / Else
    # -------------------------

    def visit_if(self, node):

        condition = self.visit(
            node.condition
        )

        # Label for else branch
        else_label = self.tac.new_label()

        # Only create an end label
        # when an else branch exists.
        end_label = None

        if node.else_branch is not None:
            end_label = self.tac.new_label()

        # ifFalse condition goto else
        self.tac.emit(
            "IF_FALSE",
            arg1=condition,
            result=else_label,
        )

        # Then branch
        self.visit(
            node.then_branch
        )

        # If there is an else branch
        if node.else_branch is not None:

            # Skip else branch
            self.tac.emit(
                "GOTO",
                result=end_label,
            )

            # Else label
            self.tac.emit(
                "LABEL",
                result=else_label,
            )

            # Else branch
            self.visit(
                node.else_branch
            )

            # End label
            self.tac.emit(
                "LABEL",
                result=end_label,
            )

        else:

            # No else branch
            self.tac.emit(
                "LABEL",
                result=else_label,
            )

    # -------------------------
    # While
    # -------------------------

    def visit_while(self, node):

        # Example:
        #
        # while (x < 10) {
        #     x = x + 1;
        # }

        start_label = self.tac.new_label()

        end_label = self.tac.new_label()

        # Loop start
        self.tac.emit(
            "LABEL",
            result=start_label,
        )

        # Generate condition
        condition = self.visit(
            node.condition
        )

        # Exit when condition is false
        self.tac.emit(
            "IF_FALSE",
            arg1=condition,
            result=end_label,
        )

        # Loop body
        self.visit(
            node.body
        )

        # Go back to beginning
        self.tac.emit(
            "GOTO",
            result=start_label,
        )

        # Loop exit
        self.tac.emit(
            "LABEL",
            result=end_label,
        )

    # -------------------------
    # Binary expression
    # -------------------------

    def visit_binary(self, node):

        left = self.visit(
            node.left
        )

        right = self.visit(
            node.right
        )

        temp = self.tac.new_temp()

        self.tac.emit(
            node.operator,
            arg1=left,
            arg2=right,
            result=temp,
        )

        return temp

    # -------------------------
    # Unary expression
    # -------------------------

    def visit_unary(self, node):

        operand = self.visit(
            node.operand
        )

        temp = self.tac.new_temp()

        self.tac.emit(
            "UNARY",
            arg1=f"{node.operator}{operand}",
            result=temp,
        )

        return temp

    # -------------------------
    # Literal
    # -------------------------

    def visit_literal(self, node):

        return self.format_literal(
            node
        )

    # -------------------------
    # Identifier
    # -------------------------

    def visit_identifier(self, node):

        return node.name

    # -------------------------
    # Literal formatting
    # -------------------------

    def format_literal(self, node):

        if node.data_type == "string":
            return f'"{node.value}"'

        if node.data_type == "bool":

            if node.value:
                return "true"

            return "false"

        return str(node.value)