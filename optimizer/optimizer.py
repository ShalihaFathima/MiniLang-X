import re

from ir.tac import TACInstruction, TACProgram


TEMP_NAME = re.compile(r"t\d+")


def collect_variable_types(program):
    """
    Map variable name -> declared type by walking the AST's
    declarations. A name declared with different types in different
    scopes maps to None (unknown), so the optimizer treats it
    conservatively.
    """
    types = {}

    def walk(node):
        if node is None:
            return

        if hasattr(node, "data_type") and hasattr(node, "initializer"):
            if node.name in types and types[node.name] != node.data_type:
                types[node.name] = None
            else:
                types[node.name] = node.data_type

        for child in getattr(node, "statements", []):
            walk(child)

        for attribute in ("then_branch", "else_branch", "body"):
            walk(getattr(node, attribute, None))

    walk(program)
    return types


class Optimizer:
    CONSTANT_OPERATORS = {
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
    }

    MAX_ROUNDS = 50

    def __init__(self, variable_types=None):
        # Declared type of each variable (see collect_variable_types).
        # Needed so a constant stored in a float variable stays a
        # float, e.g.  float f = 10;  ->  f holds 10.0
        self.variable_types = variable_types or {}

    def optimize(self, tac_program):
        instructions = tac_program.instructions

        # Repeat the passes until nothing changes (a fixed point), so
        # results of one pass feed the next:
        #   t1 = 3 * 4; t2 = 2 + t1  ->  t1 = 12; t2 = 2 + 12  ->  t2 = 14
        for _ in range(self.MAX_ROUNDS):
            previous = instructions

            instructions = self.constant_folding(instructions)
            instructions = self.constant_propagation(instructions)
            instructions = self.algebraic_simplification(instructions)

            if instructions == previous:
                break

        optimized = TACProgram()

        for instruction in instructions:
            optimized.instructions.append(instruction)

        optimized.temp_count = tac_program.temp_count
        optimized.label_count = tac_program.label_count

        return optimized

    # -------------------------------------------------
    # Constant Folding
    # -------------------------------------------------

    def constant_folding(self, instructions):
        result = []

        for instruction in instructions:

            if instruction.operation in self.CONSTANT_OPERATORS:

                if (
                    self.is_number(instruction.arg1)
                    and self.is_number(instruction.arg2)
                ):
                    left = self.parse_number(instruction.arg1)
                    right = self.parse_number(instruction.arg2)

                    # Leave division by zero for the runtime to report
                    if instruction.operation == "/" and right == 0:
                        result.append(instruction)
                        continue

                    value = self.evaluate(
                        instruction.operation,
                        left,
                        right,
                    )

                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=self.format_constant(value),
                            result=instruction.result,
                        )
                    )

                    continue

            result.append(instruction)

        return result

    # -------------------------------------------------
    # Constant Propagation
    # -------------------------------------------------

    def constant_propagation(self, instructions):
        constants = {}
        result = []

        for instruction in instructions:

            operation = instruction.operation

            # -----------------------------------------
            # Control-flow boundary
            # -----------------------------------------
            #
            # We must NOT carry constant information
            # across labels or jumps because the same
            # code may execute multiple times.
            #
            if operation in {
                "LABEL",
                "GOTO",
                "IF_FALSE",
                "IF_TRUE",
            }:
                constants.clear()

                result.append(instruction)
                continue

            # -----------------------------------------
            # Assignment
            # -----------------------------------------

            if operation == "ASSIGN":

                value = instruction.arg1

                if value in constants:
                    value = str(constants[value])

                    instruction = TACInstruction(
                        operation="ASSIGN",
                        arg1=value,
                        result=instruction.result,
                    )

                if self.is_number(value):

                    number = self.parse_number(value)
                    name = instruction.result
                    declared = self.variable_types.get(name)

                    if declared == "float":
                        constants[name] = float(number)

                    elif declared == "int" or TEMP_NAME.fullmatch(name):
                        constants[name] = number

                    else:
                        # Unknown type: do not propagate, since an int
                        # constant stored in a float variable would
                        # otherwise be treated as an int.
                        constants.pop(name, None)

                else:

                    constants.pop(
                        instruction.result,
                        None,
                    )

                result.append(instruction)

                continue

            # -----------------------------------------
            # Binary operation
            # -----------------------------------------

            if operation in self.CONSTANT_OPERATORS:

                arg1 = instruction.arg1
                arg2 = instruction.arg2

                if arg1 in constants:
                    arg1 = str(constants[arg1])

                if arg2 in constants:
                    arg2 = str(constants[arg2])

                instruction = TACInstruction(
                    operation=operation,
                    arg1=arg1,
                    arg2=arg2,
                    result=instruction.result,
                )

                result.append(instruction)

                continue

            result.append(instruction)

        return result

    # -------------------------------------------------
    # Algebraic Simplification
    # -------------------------------------------------

    def algebraic_simplification(self, instructions):
        result = []

        for instruction in instructions:

            operation = instruction.operation

            # x + 0 = x
            if operation == "+":

                if instruction.arg2 == "0":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg1,
                            result=instruction.result,
                        )
                    )
                    continue

                if instruction.arg1 == "0":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg2,
                            result=instruction.result,
                        )
                    )
                    continue

            # x - 0 = x
            if operation == "-":

                if instruction.arg2 == "0":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg1,
                            result=instruction.result,
                        )
                    )
                    continue

            # x * 1 = x
            if operation == "*":

                if instruction.arg2 == "1":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg1,
                            result=instruction.result,
                        )
                    )
                    continue

                if instruction.arg1 == "1":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg2,
                            result=instruction.result,
                        )
                    )
                    continue

            # x / 1 = x
            if operation == "/":

                if instruction.arg2 == "1":
                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=instruction.arg1,
                            result=instruction.result,
                        )
                    )
                    continue

            result.append(instruction)

        return result

    # -------------------------------------------------
    # Utility Functions
    # -------------------------------------------------

    def is_number(self, value):

        if value is None:
            return False

        try:
            float(value)
            return True

        except (ValueError, TypeError):
            return False

    def parse_number(self, value):

        # Keep the literal's type: "10" is an int, "10.0" is a float
        if any(marker in value.lower() for marker in (".", "e", "inf", "nan")):
            return float(value)

        return int(value)

    def format_constant(self, value):

        # Comparison results must use MiniLang-X boolean literals
        if isinstance(value, bool):
            return "true" if value else "false"

        return str(value)

    def evaluate(self, operator, left, right):

        if operator == "+":
            return left + right

        if operator == "-":
            return left - right

        if operator == "*":
            return left * right

        if operator == "/":

            # int / int is integer division (truncating toward zero);
            # any float operand gives floating-point division.
            if isinstance(left, int) and isinstance(right, int):
                quotient = abs(left) // abs(right)
                return quotient if (left >= 0) == (right >= 0) else -quotient

            return left / right

        if operator == "==":
            return left == right

        if operator == "!=":
            return left != right

        if operator == "<":
            return left < right

        if operator == ">":
            return left > right

        if operator == "<=":
            return left <= right

        if operator == ">=":
            return left >= right

        raise ValueError(
            f"Unsupported operator: {operator}"
        )