ARITHMETIC_OPERATIONS = {"+", "-", "*", "/"}
COMPARISON_OPERATIONS = {"==", "!=", "<", ">", "<=", ">="}
BRANCH_OPERATIONS = {"IF_FALSE", "IF_TRUE"}


def calculate_tac_statistics(tac_program):
    """
    Count TAC instructions by kind. Temporary and label counts come
    from the TACProgram's own counters.
    """
    operations = [
        instruction.operation
        for instruction in tac_program.instructions
    ]

    def count(names):
        return sum(operation in names for operation in operations)

    return {
        "instruction_count": len(operations),
        "temporary_count": tac_program.temp_count,
        "label_count": tac_program.label_count,
        "arithmetic_count": count(ARITHMETIC_OPERATIONS),
        "assignment_count": count({"ASSIGN"}),
        "comparison_count": count(COMPARISON_OPERATIONS),
        "branch_count": count(BRANCH_OPERATIONS),
        "jump_count": count({"GOTO"}),
        "print_count": count({"PRINT"}),
    }
