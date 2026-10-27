"""
MiniLang-X Parser Lab Package
Provides context-free grammar representation, validation, FIRST/FOLLOW set computation,
LL(1) table generation & parsing, and Recursive Descent parsing.
"""

from parser_lab.grammar import Grammar, Production, EPSILON, END_MARKER
from parser_lab.validation import Diagnostic, GrammarValidator, ValidationResult
from parser_lab.first_follow import FirstFollowCalculator, FirstFollowResult
from parser_lab.parse_tree import ParseTreeNode
from parser_lab.tokenizer import tokenize_input_string
from parser_lab.ll1 import LL1TableGenerator, LL1Parser, LL1TableResult, LL1ParseResult
from parser_lab.recursive_descent import (
    RecursiveDescentParser,
    LeftRecursionDetector,
    LeftRecursionReport,
    RDParseResult,
)
from parser_lab.lr_common import (
    AugmentedGrammar,
    LR0Item,
    LR1Item,
    LRAction,
    LRConflict,
    LRTraceStep,
    LRParseResult,
    LRTableResult,
    LRParserEngine,
)
from parser_lab.slr1 import SLR1TableGenerator, SLR1Parser
from parser_lab.clr1 import CLR1TableGenerator, CLR1Parser
from parser_lab.lalr1 import LALR1TableGenerator, LALR1Parser

__all__ = [
    "Grammar",
    "Production",
    "EPSILON",
    "END_MARKER",
    "Diagnostic",
    "GrammarValidator",
    "ValidationResult",
    "FirstFollowCalculator",
    "FirstFollowResult",
    "ParseTreeNode",
    "tokenize_input_string",
    "LL1TableGenerator",
    "LL1Parser",
    "LL1TableResult",
    "LL1ParseResult",
    "RecursiveDescentParser",
    "LeftRecursionDetector",
    "LeftRecursionReport",
    "RDParseResult",
    "AugmentedGrammar",
    "LR0Item",
    "LR1Item",
    "LRAction",
    "LRConflict",
    "LRTraceStep",
    "LRParseResult",
    "LRTableResult",
    "LRParserEngine",
    "SLR1TableGenerator",
    "SLR1Parser",
    "CLR1TableGenerator",
    "CLR1Parser",
    "LALR1TableGenerator",
    "LALR1Parser",
]

