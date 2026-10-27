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
    source_tokens = [
        token for token in tokens
        if token.type != TokenType.EOF
    ]

    return {
        "total_tokens": len(source_tokens),
        "identifiers": sum(
            token.type == TokenType.IDENTIFIER
            for token in source_tokens
        ),
        "keywords": sum(
            token.type in KEYWORD_TYPES
            for token in source_tokens
        ),
        "literals": sum(
            token.type in LITERAL_TYPES
            for token in source_tokens
        ),
        "operators": sum(
            token.type in OPERATOR_TYPES
            for token in source_tokens
        ),
        "separators": sum(
            token.type in SEPARATOR_TYPES
            for token in source_tokens
        ),
        "comments": comment_count,
    }
