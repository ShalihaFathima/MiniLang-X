from ir.tac import TACInstruction, TACProgram


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

    def optimize(self, tac_program):
        instructions = tac_program.instructions

        instructions = self.constant_folding(instructions)
        instructions = self.constant_propagation(instructions)
        instructions = self.algebraic_simplification(instructions)

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

                    value = self.evaluate(
                        instruction.operation,
                        left,
                        right,
                    )

                    result.append(
                        TACInstruction(
                            operation="ASSIGN",
                            arg1=str(value),
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

                    constants[instruction.result] = (
                        self.parse_number(value)
                    )

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

        number = float(value)

        if number.is_integer():
            return int(number)

        return number

    def evaluate(self, operator, left, right):

        if operator == "+":
            return left + right

        if operator == "-":
            return left - right

        if operator == "*":
            return left * right

        if operator == "/":
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