from syntax_tree.nodes import VarDeclaration, Identifier
from syntax_tree.statistics import ast_children


def calculate_semantic_statistics(ast, symbol_table, error_count=0):
    """
    Summarise a semantic analysis run.

    Symbol counts come from the symbol table, so after an error they
    reflect only the part of the program analysed before it stopped.
    Declaration and identifier-use counts come from the whole AST.
    """
    declarations = 0
    identifier_uses = 0

    stack = [ast]

    while stack:
        node = stack.pop()

        if isinstance(node, VarDeclaration):
            declarations += 1

        if isinstance(node, Identifier):
            identifier_uses += 1

        stack.extend(ast_children(node))

    variables_by_type = {}

    for symbol in symbol_table.symbols:
        variables_by_type[symbol.data_type] = (
            variables_by_type.get(symbol.data_type, 0) + 1
        )

    return {
        "symbol_count": len(symbol_table.symbols),
        "declaration_count": declarations,
        "identifier_use_count": identifier_uses,
        "scope_count": symbol_table.scope_count,
        "error_count": error_count,
        "initialized_count": sum(
            symbol.initialized for symbol in symbol_table.symbols
        ),
        "variables_by_type": variables_by_type,
    }
