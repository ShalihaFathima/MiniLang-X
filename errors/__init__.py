def source_context(source, line, column):
    """
    Return the source line containing an error with a caret under the
    error column, e.g.

        int x = 10 + );
                     ^

    Returns None when the source text or location is unavailable.
    """
    if source is None or line is None or column is None:
        return None

    lines = source.split("\n")

    if not 1 <= line <= len(lines):
        return None

    return f"{lines[line - 1]}\n{' ' * (column - 1)}^"


def format_error(title, line, column, details, context=None):
    """
    Build the multi-line message shared by lexical, syntax and
    semantic errors:

        Syntax Error
        Line: 1
        Column: 14
        Unexpected token: ')' (RPAREN)
        Source:
        int x = 10 + );
                     ^
    """
    lines = [title]

    if line is not None:
        lines.append(f"Line: {line}")

    if column is not None:
        lines.append(f"Column: {column}")

    lines.extend(details)

    if context is not None:
        lines.append("Source:")
        lines.append(context)

    return "\n".join(lines)
