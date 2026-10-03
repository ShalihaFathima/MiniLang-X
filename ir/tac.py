from dataclasses import dataclass


@dataclass
class TACInstruction:
    """
    Represents one Three Address Code instruction.

    Examples:

        x = 10
        t1 = x + y
        ifFalse t1 goto L1
        goto L2
        L1:
        print x
    """

    operation: str
    arg1: str = None
    arg2: str = None
    result: str = None

    def __str__(self):

        # Label
        if self.operation == "LABEL":
            return f"{self.result}:"

        # Unconditional jump
        if self.operation == "GOTO":
            return f"goto {self.result}"

        # Conditional jump
        if self.operation == "IF_FALSE":
            return f"ifFalse {self.arg1} goto {self.result}"

        if self.operation == "IF_TRUE":
            return f"ifTrue {self.arg1} goto {self.result}"

        # Print
        if self.operation == "PRINT":
            return f"print {self.arg1}"

        # Assignment
        if self.operation == "ASSIGN":
            return f"{self.result} = {self.arg1}"

        # Unary operation
        if self.operation == "UNARY":
            return f"{self.result} = {self.arg1}"

        # Binary operations
        binary_operations = {
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

        if self.operation in binary_operations:
            return (
                f"{self.result} = "
                f"{self.arg1} "
                f"{self.operation} "
                f"{self.arg2}"
            )

        # Return
        if self.operation == "RETURN":
            return f"return {self.arg1}"

        # Fallback
        parts = [
            self.operation,
            self.arg1,
            self.arg2,
            self.result,
        ]

        return " ".join(
            str(part)
            for part in parts
            if part is not None
        )


class TACProgram:
    """
    Stores the complete Three Address Code program.
    """

    def __init__(self):
        self.instructions = []

        self.temp_count = 0
        self.label_count = 0

    # -------------------------
    # Temporary variables
    # -------------------------

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    # -------------------------
    # Labels
    # -------------------------

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    # -------------------------
    # Emit instruction
    # -------------------------

    def emit(
        self,
        operation,
        arg1=None,
        arg2=None,
        result=None,
    ):
        instruction = TACInstruction(
            operation=operation,
            arg1=arg1,
            arg2=arg2,
            result=result,
        )

        self.instructions.append(instruction)

        return instruction

    # -------------------------
    # Display
    # -------------------------

    def __str__(self):

        if not self.instructions:
            return "<empty TAC>"

        lines = []

        for index, instruction in enumerate(
            self.instructions
        ):
            lines.append(
                f"{index:03}: {instruction}"
            )

        return "\n".join(lines)