from ir.tac import TACProgram


ARITHMETIC_OPERATIONS = {"+", "-", "*", "/"}
COMPARISON_OPERATIONS = {
    "==",
    "!=",
    "<",
    ">",
    "<=",
    ">=",
}


def calculate_tac_statistics(tac_program):
    if not isinstance(tac_program, TACProgram):
        raise TypeError(
            f"Expected TACProgram, got {type(tac_program).__name__}"
        )

    operations = [
        instruction.operation
        for instruction in tac_program.instructions
    ]

    return {
        "instruction_count": len(operations),
        "temporary_count": tac_program.temp_count,
        "label_count": sum(operation == "LABEL" for operation in operations),
        "arithmetic_count": sum(
            operation in ARITHMETIC_OPERATIONS
            for operation in operations
        ),
        "assignment_count": sum(
            operation == "ASSIGN"
            for operation in operations
        ),
        "comparison_count": sum(
            operation in COMPARISON_OPERATIONS
            for operation in operations
        ),
        "branch_count": sum(
            operation in {"IF_FALSE", "IF_TRUE"}
            for operation in operations
        ),
        "jump_count": sum(
            operation == "GOTO"
            for operation in operations
        ),
        "print_count": sum(
            operation == "PRINT"
            for operation in operations
        ),
    }
