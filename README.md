# Phase 2: Lexical Analysis

MiniLang-X transforms source code into a token stream before parsing:

```text
Source Code
    ↓
Lexical Analyzer
    ↓
Token Stream
```

The lexer classifies the language's existing keywords, identifiers,
literals, operators, and delimiters. Each token preserves its type, lexeme,
line, and column. Invalid characters and unterminated strings produce clear
lexical errors with source positions. The visualizer also reports token
statistics (excluding EOF from the total) and filters the token table by
category.

# Phase 3: Syntax Analysis and AST

The parser applies MiniLang-X's existing statement and expression grammar
to the token stream, preserving operator precedence while generating an
abstract syntax tree (AST). The visualizer presents the parser flow, AST
statistics, the dynamically rendered tree, and the parsed expression's
precedence. Syntax errors report the unexpected token, expected grammar
element, line and column, and source context when available. Parser, AST,
statistics, and visualizer API behavior are covered by the unit tests.

# Phase 4: Semantic Analysis

Semantic analysis checks declarations and identifier lookup, duplicate and
undeclared variables, existing type compatibility, numeric and boolean
operand rules, and boolean control-flow conditions. It exposes the analyzer's
symbol table with scope, initialization status, and source locations when
available, along with semantic statistics and structured errors. The
visualizer presents the semantic flow, statistics, and generated symbol
table; these behaviors are covered by semantic-analysis tests.

# Phase 5: Intermediate Code Generation

The existing TAC generator translates the AST into Three Address Code using
its generated temporaries and control-flow labels. The visualizer displays
the actual instruction fields, generated temporary and label names, and
statistics for instructions, operations, branches, jumps, and prints.
Generation is blocked when semantic analysis fails. TAC output and statistics
are covered by the unit tests.

# Phase 6: Control Flow Graph and Optimization

The existing CFG groups TAC at labels and jump boundaries into basic blocks,
then connects jump targets and fall-through paths. The visualizer renders the
actual blocks, predecessors, successors, branch edges, and CFG statistics.
The existing optimizer performs constant folding, constant propagation, and
arithmetic identity simplification; its view compares original and optimized
TAC, reports observed instruction changes, and shows count-based statistics.
CFG, optimization, and optimized-execution behavior are covered by unit tests.

# Phase 7: Backend, Virtual Machine, and Execution

The existing backend lowers optimized TAC into stack-machine instructions.
The visualizer reports actual target instructions and opcode statistics, then
shows the VM's execution trace with program counters, stack and memory
snapshots, printed output, final memory, and final stack. Runtime failures and
the configured execution-step limit are displayed as distinct statuses. Trace
recording is capped while execution retains its maximum-step safeguard.
Backend, VM, runtime-error, and execution-limit behavior are covered by tests.