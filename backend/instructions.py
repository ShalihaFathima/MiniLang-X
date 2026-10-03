from dataclasses import dataclass


@dataclass
class Instruction:
    opcode: str
    operand1: object = None
    operand2: object = None

    def __str__(self):
        parts = [self.opcode]

        if self.operand1 is not None:
            parts.append(str(self.operand1))

        if self.operand2 is not None:
            parts.append(str(self.operand2))

        return " ".join(parts)


class TargetProgram:
    def __init__(self):
        self.instructions = []

    def emit(self, opcode, operand1=None, operand2=None):
        instruction = Instruction(
            opcode=opcode,
            operand1=operand1,
            operand2=operand2,
        )

        self.instructions.append(instruction)
        return instruction

    def __str__(self):
        if not self.instructions:
            return "<empty target program>"

        return "\n".join(
            f"{index:03}: {instruction}"
            for index, instruction in enumerate(self.instructions)
        )