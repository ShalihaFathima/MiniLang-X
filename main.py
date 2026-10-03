import sys

from lexer.lexer import Lexer
from parser.parser import Parser
from semantic.analyzer import SemanticAnalyzer, SemanticError
from ir.generator import TACGenerator
from optimizer.optimizer import Optimizer, collect_variable_types
from optimizer.cfg import ControlFlowGraph
from backend.code_generator import CodeGenerator
from backend.vm import VirtualMachine


def compile_source(source, show_stages=False):
    # --------------------------------
    # Phase 1: Lexical Analysis
    # --------------------------------

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    if show_stages:
        print("=== TOKENS ===")

        for token in tokens:
            print(token)

    # --------------------------------
    # Phase 2: Syntax Analysis
    # --------------------------------

    parser = Parser(tokens)
    ast = parser.parse()

    if show_stages:
        print("\n=== AST ===")
        print(ast.pretty_print())

    # --------------------------------
    # Phase 3: Semantic Analysis
    # --------------------------------

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if show_stages:
        print("\n=== SYMBOL TABLE ===")
        print(analyzer.symbol_table)

    # --------------------------------
    # Phase 4: Intermediate Code
    # --------------------------------

    tac_generator = TACGenerator()
    tac = tac_generator.generate(ast)

    if show_stages:
        print("\n=== ORIGINAL TAC ===")
        print(tac)

    # --------------------------------
    # Phase 5: Optimization
    # --------------------------------

    variable_types = collect_variable_types(ast)

    optimizer = Optimizer(variable_types)
    optimized_tac = optimizer.optimize(tac)

    if show_stages:
        print("\n=== OPTIMIZED TAC ===")
        print(optimized_tac)

        print("\n=== CONTROL FLOW GRAPH ===")

        cfg = ControlFlowGraph(
            optimized_tac.instructions
        )

        print(cfg)

    # --------------------------------
    # Phase 6: Target Code Generation
    # --------------------------------

    code_generator = CodeGenerator(variable_types)

    target_program = code_generator.generate(
        optimized_tac
    )

    if show_stages:
        print("\n=== TARGET CODE ===")
        print(target_program)

    # --------------------------------
    # Phase 7: Runtime
    # --------------------------------

    vm = VirtualMachine(target_program)

    print("\n=== PROGRAM OUTPUT ===")

    vm.run()

    return {
        "tokens": tokens,
        "ast": ast,
        "symbol_table": analyzer.symbol_table,
        "tac": tac,
        "optimized_tac": optimized_tac,
        "target_program": target_program,
        "memory": vm.memory,
    }


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 main.py <source_file>")
        print("  python3 main.py <source_file> --debug")
        return

    filename = sys.argv[1]

    show_stages = "--debug" in sys.argv

    try:

        # --------------------------------
        # Read source file
        # --------------------------------

        with open(filename, "r") as file:
            source = file.read()

        print(f"Compiling: {filename}")

        # --------------------------------
        # Compile
        # --------------------------------

        compile_source(
            source,
            show_stages=show_stages,
        )

        print("\nCompilation completed successfully.")

    except FileNotFoundError:

        print(
            f"Error: File not found: {filename}"
        )

        sys.exit(1)

    except (
        SyntaxError,
        RuntimeError,
        SemanticError,
    ) as error:

        print(
            f"\nCompilation Error: {error}"
        )

        sys.exit(1)

    except Exception as error:

        print(
            f"\nUnexpected Error: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()