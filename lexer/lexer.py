from lexer.token import Token, TokenType


class Lexer:
    KEYWORDS = {
        "int": TokenType.INT,
        "float": TokenType.FLOAT,
        "bool": TokenType.BOOL,
        "string": TokenType.STRING,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "while": TokenType.WHILE,
        "print": TokenType.PRINT,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
    }

    SINGLE_CHAR_TOKENS = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.MULTIPLY,
        "/": TokenType.DIVIDE,
        "=": TokenType.ASSIGN,
        "<": TokenType.LESS,
        ">": TokenType.GREATER,
        "!": TokenType.NOT,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
        ";": TokenType.SEMICOLON,
    }

    def __init__(self, source):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def current_char(self):
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def peek_char(self):
        if self.position + 1 >= len(self.source):
            return None
        return self.source[self.position + 1]

    def advance(self):
        char = self.current_char()

        if char is None:
            return None

        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def add_token(self, token_type, value, line, column):
        self.tokens.append(
            Token(token_type, value, line, column)
        )

    def skip_whitespace(self):
        while True:
            char = self.current_char()

            if char is None:
                return

            if char in " \t\r":
                self.advance()

            elif char == "\n":
                self.advance()

            else:
                return

    def skip_comment(self):
        # Current position is at the first '/'
        self.advance()
        self.advance()

        while self.current_char() is not None:
            if self.current_char() == "\n":
                break
            self.advance()

    def read_identifier(self):
        start_line = self.line
        start_column = self.column
        value = ""

        while True:
            char = self.current_char()

            if char is None:
                break

            if char.isalnum() or char == "_":
                value += self.advance()
            else:
                break

        token_type = self.KEYWORDS.get(
            value,
            TokenType.IDENTIFIER
        )

        self.add_token(
            token_type,
            value,
            start_line,
            start_column
        )

    def read_number(self):
        start_line = self.line
        start_column = self.column
        value = ""

        while self.current_char() is not None and self.current_char().isdigit():
            value += self.advance()

        # Check for floating-point number
        if (
            self.current_char() == "."
            and self.peek_char() is not None
            and self.peek_char().isdigit()
        ):
            value += self.advance()

            while (
                self.current_char() is not None
                and self.current_char().isdigit()
            ):
                value += self.advance()

            token_type = TokenType.FLOAT_LITERAL
        else:
            token_type = TokenType.INTEGER

        self.add_token(
            token_type,
            value,
            start_line,
            start_column
        )

    def read_string(self):
        start_line = self.line
        start_column = self.column

        # Skip opening quote
        self.advance()

        value = ""

        while self.current_char() is not None:
            char = self.current_char()

            if char == '"':
                self.advance()

                self.add_token(
                    TokenType.STRING_LITERAL,
                    value,
                    start_line,
                    start_column
                )
                return

            if char == "\n":
                raise SyntaxError(
                    f"Unterminated string at "
                    f"line {start_line}, column {start_column}"
                )

            value += self.advance()

        raise SyntaxError(
            f"Unterminated string at "
            f"line {start_line}, column {start_column}"
        )

    def tokenize(self):
        while self.current_char() is not None:

            self.skip_whitespace()

            char = self.current_char()

            if char is None:
                break

            # Comments
            if char == "/" and self.peek_char() == "/":
                self.skip_comment()
                continue

            # Identifiers and keywords
            if char.isalpha() or char == "_":
                self.read_identifier()
                continue

            # Numbers
            if char.isdigit():
                self.read_number()
                continue

            # Strings
            if char == '"':
                self.read_string()
                continue

            start_line = self.line
            start_column = self.column

            # Two-character operators
            if char == "=" and self.peek_char() == "=":
                self.advance()
                self.advance()
                self.add_token(
                    TokenType.EQUAL,
                    "==",
                    start_line,
                    start_column
                )
                continue

            if char == "!" and self.peek_char() == "=":
                self.advance()
                self.advance()
                self.add_token(
                    TokenType.NOT_EQUAL,
                    "!=",
                    start_line,
                    start_column
                )
                continue

            if char == "<" and self.peek_char() == "=":
                self.advance()
                self.advance()
                self.add_token(
                    TokenType.LESS_EQUAL,
                    "<=",
                    start_line,
                    start_column
                )
                continue

            if char == ">" and self.peek_char() == "=":
                self.advance()
                self.advance()
                self.add_token(
                    TokenType.GREATER_EQUAL,
                    ">=",
                    start_line,
                    start_column
                )
                continue

            # Single-character tokens
            token_type = self.SINGLE_CHAR_TOKENS.get(char)

            if token_type is not None:
                self.advance()

                self.add_token(
                    token_type,
                    char,
                    start_line,
                    start_column
                )
                continue

            # Unknown character
            raise SyntaxError(
                f"Unexpected character {char!r} "
                f"at line {start_line}, column {start_column}"
            )

        self.tokens.append(
            Token(
                TokenType.EOF,
                "",
                self.line,
                self.column
            )
        )

        return self.tokens