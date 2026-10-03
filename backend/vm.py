class VirtualMachine:
    def __init__(self, program):
        self.program = program
        self.instructions = program.instructions

        self.stack = []
        self.memory = {}

        self.pc = 0
        self.running = True

        self.labels = {}

        self.build_label_table()

    def build_label_table(self):
        for index, instruction in enumerate(self.instructions):
            if instruction.opcode == "LABEL":
                self.labels[instruction.operand1] = index

    def run(self):
        while self.running and self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            self.execute(instruction)

        return self.memory

    def execute(self, instruction):
        opcode = instruction.opcode

        # -------------------------
        # Stack operations
        # -------------------------

        if opcode == "PUSH":
            self.stack.append(instruction.operand1)
            self.pc += 1
            return

        if opcode == "POP":
            if not self.stack:
                raise RuntimeError("Stack underflow")

            self.stack.pop()
            self.pc += 1
            return

        # -------------------------
        # Memory operations
        # -------------------------

        if opcode == "LOAD":
            variable = instruction.operand1

            if variable not in self.memory:
                raise RuntimeError(
                    f"Variable '{variable}' has no value"
                )

            self.stack.append(self.memory[variable])
            self.pc += 1
            return

        if opcode == "STORE":
            variable = instruction.operand1

            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during STORE"
                )

            value = self.stack.pop()

            # STORE x float: the variable is declared float
            if instruction.operand2 == "float":
                value = float(value)

            self.memory[variable] = value

            self.pc += 1
            return

        # -------------------------
        # Arithmetic operations
        # -------------------------

        if opcode == "ADD":
            left, right = self.pop_two()

            self.stack.append(left + right)

            self.pc += 1
            return

        if opcode == "SUB":
            left, right = self.pop_two()

            self.stack.append(left - right)

            self.pc += 1
            return

        if opcode == "MUL":
            left, right = self.pop_two()

            self.stack.append(left * right)

            self.pc += 1
            return

        if opcode == "DIV":
            left, right = self.pop_two()

            if right == 0:
                raise RuntimeError(
                    "Division by zero"
                )

            self.stack.append(self.divide(left, right))

            self.pc += 1
            return

        # -------------------------
        # Unary operations
        # -------------------------

        if opcode == "NEG":
            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during NEG"
                )

            value = self.stack.pop()

            self.stack.append(-value)

            self.pc += 1
            return

        if opcode == "NOT":
            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during NOT"
                )

            value = self.stack.pop()

            self.stack.append(not value)

            self.pc += 1
            return

        # -------------------------
        # Comparison operations
        # -------------------------

        if opcode == "CMP_EQ":
            left, right = self.pop_two()

            self.stack.append(left == right)

            self.pc += 1
            return

        if opcode == "CMP_NE":
            left, right = self.pop_two()

            self.stack.append(left != right)

            self.pc += 1
            return

        if opcode == "CMP_LT":
            left, right = self.pop_two()

            self.stack.append(left < right)

            self.pc += 1
            return

        if opcode == "CMP_GT":
            left, right = self.pop_two()

            self.stack.append(left > right)

            self.pc += 1
            return

        if opcode == "CMP_LE":
            left, right = self.pop_two()

            self.stack.append(left <= right)

            self.pc += 1
            return

        if opcode == "CMP_GE":
            left, right = self.pop_two()

            self.stack.append(left >= right)

            self.pc += 1
            return

        # -------------------------
        # Unconditional jump
        # -------------------------

        if opcode == "JMP":
            label = instruction.operand1

            if label not in self.labels:
                raise RuntimeError(
                    f"Unknown label: {label}"
                )

            self.pc = self.labels[label]

            return

        # -------------------------
        # Conditional jump
        # -------------------------

        if opcode == "JMP_IF_FALSE":
            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during JMP_IF_FALSE"
                )

            condition = self.stack.pop()

            if not condition:
                label = instruction.operand1

                if label not in self.labels:
                    raise RuntimeError(
                        f"Unknown label: {label}"
                    )

                self.pc = self.labels[label]

            else:
                self.pc += 1

            return

        if opcode == "JMP_IF_TRUE":
            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during JMP_IF_TRUE"
                )

            condition = self.stack.pop()

            if condition:
                label = instruction.operand1

                if label not in self.labels:
                    raise RuntimeError(
                        f"Unknown label: {label}"
                    )

                self.pc = self.labels[label]

            else:
                self.pc += 1

            return

        # -------------------------
        # Label
        # -------------------------

        if opcode == "LABEL":
            self.pc += 1
            return

        # -------------------------
        # Print
        # -------------------------

        if opcode == "PRINT":
            if not self.stack:
                raise RuntimeError(
                    "Stack underflow during PRINT"
                )

            value = self.stack.pop()

            print(value)

            self.pc += 1
            return

        # -------------------------
        # Program termination
        # -------------------------

        if opcode == "HALT":
            self.running = False
            return

        # -------------------------
        # Unknown instruction
        # -------------------------

        raise RuntimeError(
            f"Unknown VM instruction: {opcode}"
        )

    def divide(self, left, right):
        # int / int is integer division truncating toward zero;
        # if either operand is a float, use floating-point division.
        if isinstance(left, int) and isinstance(right, int):
            quotient = abs(left) // abs(right)
            return quotient if (left >= 0) == (right >= 0) else -quotient

        return left / right

    def pop_two(self):
        if len(self.stack) < 2:
            raise RuntimeError(
                "Stack underflow"
            )

        right = self.stack.pop()
        left = self.stack.pop()

        return left, right