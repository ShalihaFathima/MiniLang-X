from dataclasses import dataclass
from typing import Any


class ASTNode:
    """Base class for all AST nodes."""

    def pretty_print(self, indent=0):
        raise NotImplementedError


@dataclass
class Program(ASTNode):
    statements: list

    def pretty_print(self, indent=0):
        lines = [" " * indent + "Program"]

        for statement in self.statements:
            lines.append(statement.pretty_print(indent + 2))

        return "\n".join(lines)


@dataclass
class Block(ASTNode):
    statements: list

    def pretty_print(self, indent=0):
        lines = [" " * indent + "Block"]

        for statement in self.statements:
            lines.append(statement.pretty_print(indent + 2))

        return "\n".join(lines)


@dataclass
class VarDeclaration(ASTNode):
    data_type: str
    name: str
    initializer: Any = None

    def pretty_print(self, indent=0):
        lines = [
            " " * indent
            + f"Declaration: {self.name} : {self.data_type}"
        ]

        if self.initializer:
            lines.append(
                self.initializer.pretty_print(indent + 2)
            )

        return "\n".join(lines)


@dataclass
class Assignment(ASTNode):
    name: str
    expression: Any

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + f"Assignment: {self.name}\n"
            + self.expression.pretty_print(indent + 2)
        )


@dataclass
class PrintStatement(ASTNode):
    expression: Any

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + "Print\n"
            + self.expression.pretty_print(indent + 2)
        )


@dataclass
class IfStatement(ASTNode):
    condition: Any
    then_branch: Block
    else_branch: Block = None

    def pretty_print(self, indent=0):
        lines = [
            " " * indent + "If",
            self.condition.pretty_print(indent + 2),
            self.then_branch.pretty_print(indent + 2),
        ]

        if self.else_branch:
            lines.append(
                self.else_branch.pretty_print(indent + 2)
            )

        return "\n".join(lines)


@dataclass
class WhileStatement(ASTNode):
    condition: Any
    body: Block

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + "While\n"
            + self.condition.pretty_print(indent + 2)
            + "\n"
            + self.body.pretty_print(indent + 2)
        )


@dataclass
class BinaryExpression(ASTNode):
    left: Any
    operator: str
    right: Any

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + f"Binary: {self.operator}\n"
            + self.left.pretty_print(indent + 2)
            + "\n"
            + self.right.pretty_print(indent + 2)
        )


@dataclass
class UnaryExpression(ASTNode):
    operator: str
    operand: Any

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + f"Unary: {self.operator}\n"
            + self.operand.pretty_print(indent + 2)
        )


@dataclass
class Literal(ASTNode):
    data_type: str
    value: Any

    def pretty_print(self, indent=0):
        return (
            " " * indent
            + f"Literal: {self.value} ({self.data_type})"
        )


@dataclass
class Identifier(ASTNode):
    name: str

    def pretty_print(self, indent=0):
        return " " * indent + f"Identifier: {self.name}"