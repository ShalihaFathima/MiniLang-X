from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # Keywords
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()
    # Identifiers and literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()

    ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    GREATER = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()

    NOT = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMICOLON = auto()

    # Special
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return (
            f"{self.type.name:<16} "
            f"{self.value!r:<15} "
            f"line={self.line:<3} "
            f"column={self.column}"
        )