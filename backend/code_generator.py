from ir.tac import TACProgram
from backend.instructions import TargetProgram


class CodeGenerator:
    def __init__(self, variable_types=None):
        self.target = TargetProgram()

        # Declared type of each variable (from the AST). Stores into
        # float variables are tagged so the VM keeps the value a float,
        # e.g.  float g = 10;  stores 10.0
        self.variable_types = variable_types or {}

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
            self.store(instruction.result)
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

    def store(self, name):
        if self.variable_types.get(name) == "float":
            self.target.emit("STORE", name, "float")
        else:
            self.target.emit("STORE", name)

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
        self.store(instruction.result)

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

        self.store(instruction.result)

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

        # Keep the literal's type: "7" is an int, "7.0" is a float
        if any(marker in value.lower() for marker in (".", "e", "inf", "nan")):
            return float(value)

        return int(value)