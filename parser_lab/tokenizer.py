"""
MiniLang-X Parser Lab — Input String Tokenizer for Parsers
Tokenizes user-supplied input strings into a sequence of grammar terminals.
"""

from __future__ import annotations

import re
from typing import Sequence


def tokenize_input_string(
    input_text: str, terminals: Sequence[str]
) -> tuple[list[str], list[str]]:
    """
    Tokenizes user input string against known grammar terminals.
    Supports whitespace-separated tokens (e.g. 'id + id') and compact input (e.g. 'id+id').

    Returns (tokens, errors).
    """
    cleaned = input_text.strip()
    if not cleaned:
        return [], []

    # Sort terminals by length descending for maximal munch (e.g. '==' before '=')
    sorted_terminals = sorted(terminals, key=len, reverse=True)

    tokens: list[str] = []
    errors: list[str] = []
    i = 0
    n = len(input_text)

    while i < n:
        # Skip whitespace
        if input_text[i].isspace():
            i += 1
            continue

        matched_term = None
        for term in sorted_terminals:
            if not term:
                continue

            if input_text.startswith(term, i):
                # If terminal is alphanumeric / identifier-like, ensure we don't match a prefix of a longer identifier
                # unless term itself ends at a non-identifier boundary
                if re.match(r"^[A-Za-z0-9_]+$", term):
                    next_idx = i + len(term)
                    if next_idx < n and (
                        input_text[next_idx].isalnum() or input_text[next_idx] == "_"
                    ):
                        # E.g. terminal is 'i', but input has 'id' -> do not match 'i'
                        continue
                matched_term = term
                break

        if matched_term is not None:
            tokens.append(matched_term)
            i += len(matched_term)
        else:
            # Capture the unrecognized segment
            m = re.match(r"\S+", input_text[i:])
            unrecognized = m.group(0) if m else input_text[i]
            errors.append(
                f"Unrecognized token '{unrecognized}' at position {i + 1}."
            )
            i += len(unrecognized)

    return tokens, errors
