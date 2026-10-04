from backend.instructions import TargetProgram


ARITHMETIC_OPCODES = {"ADD", "SUB", "MUL", "DIV", "NEG"}
COMPARISON_OPCODES = {
    "CMP_EQ",
    "CMP_NE",
    "CMP_LT",
    "CMP_GT",
    "CMP_LE",
    "CMP_GE",
}
JUMP_OPCODES = {"JMP", "JMP_IF_FALSE", "JMP_IF_TRUE"}


def calculate_backend_statistics(target_program):
    if not isinstance(target_program, TargetProgram):
        raise TypeError(
            f"Expected TargetProgram, got {type(target_program).__name__}"
        )

    opcodes = [
        instruction.opcode
        for instruction in target_program.instructions
    ]
    return {
        "target_instruction_count": len(opcodes),
        "label_count": opcodes.count("LABEL"),
        "load_count": opcodes.count("LOAD"),
        "push_count": opcodes.count("PUSH"),
        "store_count": opcodes.count("STORE"),
        "memory_operation_count": opcodes.count("LOAD") + opcodes.count("STORE"),
        "arithmetic_count": sum(opcode in ARITHMETIC_OPCODES for opcode in opcodes),
        "comparison_count": sum(opcode in COMPARISON_OPCODES for opcode in opcodes),
        "jump_count": sum(opcode in JUMP_OPCODES for opcode in opcodes),
        "conditional_branch_count": sum(
            opcode in {"JMP_IF_FALSE", "JMP_IF_TRUE"}
            for opcode in opcodes
        ),
        "print_count": opcodes.count("PRINT"),
        "halt_count": opcodes.count("HALT"),
    }
