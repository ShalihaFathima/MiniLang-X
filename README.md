# MiniLang-X Interactive Compiler Lab

MiniLang-X is an educational compiler implementation for demonstrating the
major stages of a compiler using a small, statically typed language. The
project includes a Python command-line compiler and a Flask visualizer backed
by the same lexer, parser, semantic analyzer, intermediate representation,
optimizer, target-code generator, and virtual machine.

## Compiler pipeline

```text
Source → Lexer → Parser → Precedence / AST → Semantic Analysis
       → TAC → CFG → Optimizer → Backend → Virtual Machine → Output
```

## Setup and running

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Compile and execute a source file with the command-line compiler:

```powershell
python main.py tests/arithmetic.minix
```

Start the interactive compiler lab:

```powershell
python -m visualizer.app
```

Open `http://127.0.0.1:5000/` in a browser. Enter or paste MiniLang-X code in
the source editor, then use **Compile**, **Run**, or **Run All**. Click a
pipeline stage to inspect it directly; **Previous** and **Next Step** navigate
the pipeline. **Reset** clears stage results while preserving editor contents.
Keyboard shortcuts are Ctrl+Enter to compile, F5 to run, F10 for Next Step,
and Escape to reset.

Run the complete unit test suite:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The automated compiler test programs are `tests/arithmetic.minix`,
`tests/condition.minix`, `tests/error.minix`, `tests/sample.minix`, and
`tests/types.minix`.

## Compiler components

- **Phases 1–2:** Project setup and lexical analysis, including source
  positions, diagnostics, and token statistics.
- **Phase 3:** Recursive-descent syntax analysis, AST construction, parser
  diagnostics, and expression precedence visualization.
- **Phase 4:** Semantic checks, symbol/scope information, and diagnostics.
- **Phase 5:** Three Address Code generation, temporaries, labels, and TAC
  statistics.
- **Phase 6:** Basic-block CFG construction, graph statistics, and the
  existing constant-folding, constant-propagation, and arithmetic-identity
  optimization passes.
- **Phase 7:** Stack-machine target code, backend statistics, VM execution
  trace, stack and memory snapshots, output, and execution limits.
- **Phase 8:** The Interactive Compiler Lab, stage navigation, and reset
  workflow.

## Viva / demonstration flow

1. Open the MiniLang-X visualizer.
2. Enter or paste a MiniLang-X program in the source editor.
3. Select **Compile** and inspect tokens, parser output, precedence, AST,
   semantic results, TAC, CFG, optimizer output, and backend code.
4. Use **Run** to execute, or use **Run All** to step through the pipeline.
5. View VM execution state and the program output.
6. Use an invalid program to demonstrate compiler diagnostics.
7. Use **Reset** to clear results before another run.

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

# Phase 8: Interactive Compiler Lab

The Flask visualizer provides a compact IDE-style lab with a line-numbered
source editor, clickable compiler pipeline, and stage result panel. It renders
the actual AST, CFG, TAC, optimization comparison, backend instructions, and
VM trace returned by the existing compiler. Statistics, diagnostics, and
execution details are shown in the corresponding stage views. Compile, Run,
Run All, Previous, Next Step, and Reset controls are available; keyboard
shortcuts are Ctrl+Enter (compile), F5 (run), F10 (Next Step), and Escape
(reset). Editing source invalidates prior results, and errors remain visible
in the diagnostics view. VM execution continues to use the existing
100,000-step limit and 300-entry trace cap. The editor is intentionally a
lightweight textarea with line numbers and does not use an external editor
framework or syntax-highlighting dependency. The `.minix` files under
`tests/` remain automated compiler test programs.