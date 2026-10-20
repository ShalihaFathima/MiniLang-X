from lexer.token import TokenType


KEYWORD_TYPES = {
    TokenType.INT,
    TokenType.FLOAT,
    TokenType.BOOL,
    TokenType.STRING,
    TokenType.IF,
    TokenType.ELSE,
    TokenType.WHILE,
    TokenType.PRINT,
}

# true and false are boolean literals
LITERAL_TYPES = {
    TokenType.INTEGER,
    TokenType.FLOAT_LITERAL,
    TokenType.STRING_LITERAL,
    TokenType.TRUE,
    TokenType.FALSE,
}

OPERATOR_TYPES = {
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.MULTIPLY,
    TokenType.DIVIDE,
    TokenType.ASSIGN,
    TokenType.EQUAL,
    TokenType.NOT_EQUAL,
    TokenType.LESS,
    TokenType.GREATER,
    TokenType.LESS_EQUAL,
    TokenType.GREATER_EQUAL,
    TokenType.NOT,
}

SEPARATOR_TYPES = {
    TokenType.LPAREN,
    TokenType.RPAREN,
    TokenType.LBRACE,
    TokenType.RBRACE,
    TokenType.SEMICOLON,
}


def calculate_token_statistics(tokens, comment_count=0):
    """
    Count the tokens produced by the lexer by category. The EOF token
    is not counted. Comments produce no tokens, so their count comes
    from the lexer (Lexer.comment_count).
    """
    tokens = [token for token in tokens if token.type != TokenType.EOF]

    def count(types):
        return sum(token.type in types for token in tokens)

    return {
        "total_tokens": len(tokens),
        "identifiers": count({TokenType.IDENTIFIER}),
        "keywords": count(KEYWORD_TYPES),
        "literals": count(LITERAL_TYPES),
        "operators": count(OPERATOR_TYPES),
        "separators": count(SEPARATOR_TYPES),
        "comments": comment_count,
    }
