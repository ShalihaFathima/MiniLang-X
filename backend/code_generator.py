from ir.tac import TACProgram
from backend.instructions import TargetProgram


class CodeGenerator:
    def __init__(self):
        self.target = TargetProgram()

    def generate(self, tac_program):
        for instruction in tac_program.instructions:
            self.translate(instruction)

        self.target.emit("HALT")

        return self.target

    def translate(self, instruction):
        operation = instruction.operation

        if operation == "LABEL":
            self.target.emit("LABEL", instruction.result)
            return

        if operation == "GOTO":
            self.target.emit("JMP", instruction.result)
            return

        if operation == "IF_FALSE":
            self.load_operand(instruction.arg1)
            self.target.emit("JMP_IF_FALSE", instruction.result)
            return

        if operation == "IF_TRUE":
            self.load_operand(instruction.arg1)
            self.target.emit("JMP_IF_TRUE", instruction.result)
            return

        if operation == "PRINT":
            self.load_operand(instruction.arg1)
            self.target.emit("PRINT")
            return

        if operation == "ASSIGN":
            self.load_operand(instruction.arg1)
            self.target.emit("STORE", instruction.result)
            return

        if operation == "UNARY":
            self.translate_unary(instruction)
            return

        if operation in {
            "+",
            "-",
            "*",
            "/",
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
        }:
            self.translate_binary(instruction)
            return

        raise RuntimeError(
            f"Unsupported TAC operation: {operation}"
        )

    def load_operand(self, operand):
        if self.is_literal(operand):
            self.target.emit("PUSH", self.parse_literal(operand))
        else:
            self.target.emit("LOAD", operand)

    def translate_binary(self, instruction):
        self.load_operand(instruction.arg1)
        self.load_operand(instruction.arg2)

        opcode_map = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV",
            "==": "CMP_EQ",
            "!=": "CMP_NE",
            "<": "CMP_LT",
            ">": "CMP_GT",
            "<=": "CMP_LE",
            ">=": "CMP_GE",
        }

        opcode = opcode_map[instruction.operation]

        self.target.emit(opcode)
        self.target.emit("STORE", instruction.result)

    def translate_unary(self, instruction):
        expression = instruction.arg1

        if expression.startswith("-"):
            operand = expression[1:]
            self.load_operand(operand)
            self.target.emit("NEG")

        elif expression.startswith("!"):
            operand = expression[1:]
            self.load_operand(operand)
            self.target.emit("NOT")

        else:
            raise RuntimeError(
                f"Unsupported unary expression: {expression}"
            )

        self.target.emit("STORE", instruction.result)

    def is_literal(self, value):
        if value is None:
            return False

        if value == "true" or value == "false":
            return True

        if value.startswith('"') and value.endswith('"'):
            return True

        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def parse_literal(self, value):
        if value == "true":
            return True

        if value == "false":
            return False

        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        number = float(value)

        if number.is_integer():
            return int(number)

        return number