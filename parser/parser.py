from lexer.token import TokenType

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


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current_token(self):
        if self.position >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[self.position]

    def peek_token(self, offset=1):
        index = self.position + offset

        if index >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[index]

    def advance(self):
        token = self.current_token()

        if self.position < len(self.tokens) - 1:
            self.position += 1

        return token

    def check(self, *token_types):
        return self.current_token().type in token_types

    def match(self, *token_types):
        if self.current_token().type in token_types:
            return self.advance()

        return None

    def expect(self, token_type):
        token = self.current_token()

        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}, "
                f"but found {token.type.name} "
                f"({token.value!r}) "
                f"at line {token.line}, column {token.column}"
            )

        return self.advance()

    # -------------------------
    # Program
    # -------------------------

    def parse(self):
        statements = []

        while not self.check(TokenType.EOF):
            statements.append(self.parse_statement())

        return Program(statements)

    # -------------------------
    # Statements
    # -------------------------

    def parse_statement(self):
        if self.check(
            TokenType.INT,
            TokenType.FLOAT,
            TokenType.BOOL,
            TokenType.STRING,
        ):
            return self.parse_declaration()

        if self.check(TokenType.IF):
            return self.parse_if_statement()

        if self.check(TokenType.WHILE):
            return self.parse_while_statement()

        if self.check(TokenType.PRINT):
            return self.parse_print_statement()

        if self.check(TokenType.IDENTIFIER):
            return self.parse_assignment()

        token = self.current_token()

        raise SyntaxError(
            f"Unexpected token {token.value!r} "
            f"at line {token.line}, "
            f"column {token.column}"
        )

    def parse_declaration(self):
        variable_type = self.advance()
        name = self.expect(TokenType.IDENTIFIER)

        initializer = None

        if self.match(TokenType.ASSIGN):
            initializer = self.parse_expression()

        self.expect(TokenType.SEMICOLON)

        return VarDeclaration(
            data_type=variable_type.value,
            name=name.value,
            initializer=initializer,
        )

    def parse_assignment(self):
        name = self.expect(TokenType.IDENTIFIER)

        self.expect(TokenType.ASSIGN)

        expression = self.parse_expression()

        self.expect(TokenType.SEMICOLON)

        return Assignment(
            name=name.value,
            expression=expression,
        )

    def parse_if_statement(self):
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)

        condition = self.parse_expression()

        self.expect(TokenType.RPAREN)

        then_branch = self.parse_block()

        else_branch = None

        if self.match(TokenType.ELSE):
            else_branch = self.parse_block()

        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def parse_while_statement(self):
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)

        condition = self.parse_expression()

        self.expect(TokenType.RPAREN)

        body = self.parse_block()

        return WhileStatement(
            condition=condition,
            body=body,
        )

    def parse_print_statement(self):
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)

        expression = self.parse_expression()

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)

        return PrintStatement(
            expression=expression
        )

    def parse_block(self):
        self.expect(TokenType.LBRACE)

        statements = []

        while not self.check(TokenType.RBRACE):
            if self.check(TokenType.EOF):
                raise SyntaxError(
                    "Expected '}' before end of file"
                )

            statements.append(self.parse_statement())

        self.expect(TokenType.RBRACE)

        return Block(statements)

    # -------------------------
    # Expressions
    # -------------------------

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        expression = self.parse_term()

        while self.check(
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.LESS,
            TokenType.GREATER,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
        ):
            operator = self.advance()
            right = self.parse_term()

            expression = BinaryExpression(
                left=expression,
                operator=operator.value,
                right=right,
            )

        return expression

    def parse_term(self):
        expression = self.parse_factor()

        while self.check(
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = self.advance()
            right = self.parse_factor()

            expression = BinaryExpression(
                left=expression,
                operator=operator.value,
                right=right,
            )

        return expression

    def parse_factor(self):
        expression = self.parse_unary()

        while self.check(
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        ):
            operator = self.advance()
            right = self.parse_unary()

            expression = BinaryExpression(
                left=expression,
                operator=operator.value,
                right=right,
            )

        return expression

    def parse_unary(self):
        if self.check(
            TokenType.MINUS,
            TokenType.NOT,
        ):
            operator = self.advance()

            operand = self.parse_unary()

            return UnaryExpression(
                operator=operator.value,
                operand=operand,
            )

        return self.parse_primary()

    def parse_primary(self):
        token = self.current_token()

        if self.match(TokenType.INTEGER):
            return Literal(
                data_type="int",
                value=token.value,
            )

        if self.match(TokenType.FLOAT_LITERAL):
            return Literal(
                data_type="float",
                value=token.value,
            )

        if self.match(TokenType.STRING_LITERAL):
            return Literal(
                data_type="string",
                value=token.value,
            )

        if self.match(TokenType.TRUE):
            return Literal(
                data_type="bool",
                value=True,
            )

        if self.match(TokenType.FALSE):
            return Literal(
                data_type="bool",
                value=False,
            )

        if self.match(TokenType.IDENTIFIER):
            return Identifier(
                name=token.value
            )

        if self.match(TokenType.LPAREN):
            expression = self.parse_expression()

            self.expect(TokenType.RPAREN)

            return expression

        raise SyntaxError(
            f"Expected expression, "
            f"but found {token.type.name} "
            f"({token.value!r}) "
            f"at line {token.line}, "
            f"column {token.column}"
        )