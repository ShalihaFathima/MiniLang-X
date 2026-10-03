class BasicBlock:
    def __init__(self, block_id):
        self.block_id = block_id
        self.instructions = []

        self.successors = []
        self.predecessors = []

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

    def add_successor(self, block):
        if block not in self.successors:
            self.successors.append(block)

    def add_predecessor(self, block):
        if block not in self.predecessors:
            self.predecessors.append(block)

    def __str__(self):
        lines = [
            f"Block B{self.block_id}:"
        ]

        for instruction in self.instructions:
            lines.append(
                f"    {instruction}"
            )

        successors = [
            f"B{block.block_id}"
            for block in self.successors
        ]

        if successors:
            lines.append(
                f"    → {', '.join(successors)}"
            )

        return "\n".join(lines)


class ControlFlowGraph:
    def __init__(self, instructions):
        self.instructions = instructions
        self.blocks = []

        self.build()

    # -------------------------
    # Find leaders
    # -------------------------

    def find_leaders(self):
        leaders = {0}

        label_to_index = {}

        for index, instruction in enumerate(
            self.instructions
        ):
            if instruction.operation == "LABEL":
                label_to_index[
                    instruction.result
                ] = index

        for index, instruction in enumerate(
            self.instructions
        ):
            # Instructions following jumps
            if instruction.operation in {
                "GOTO",
                "IF_FALSE",
                "IF_TRUE",
            }:
                if index + 1 < len(
                    self.instructions
                ):
                    leaders.add(index + 1)

                # Jump target
                target = instruction.result

                if target in label_to_index:
                    leaders.add(
                        label_to_index[target]
                    )

        return sorted(leaders)

    # -------------------------
    # Build basic blocks
    # -------------------------

    def build(self):
        if not self.instructions:
            return

        leaders = self.find_leaders()

        for i, start in enumerate(leaders):

            if i + 1 < len(leaders):
                end = leaders[i + 1]
            else:
                end = len(self.instructions)

            block = BasicBlock(i)

            for instruction in self.instructions[
                start:end
            ]:
                block.add_instruction(
                    instruction
                )

            self.blocks.append(block)

        self.connect_blocks()

    # -------------------------
    # Connect blocks
    # -------------------------

    def connect_blocks(self):

        label_to_block = {}

        for block in self.blocks:
            for instruction in block.instructions:

                if instruction.operation == "LABEL":
                    label_to_block[
                        instruction.result
                    ] = block

        for index, block in enumerate(
            self.blocks
        ):

            if not block.instructions:
                continue

            last = block.instructions[-1]

            # Unconditional jump
            if last.operation == "GOTO":

                target = label_to_block.get(
                    last.result
                )

                if target:
                    block.add_successor(
                        target
                    )

                    target.add_predecessor(
                        block
                    )

                continue

            # Conditional jump
            if last.operation in {
                "IF_FALSE",
                "IF_TRUE",
            }:

                target = label_to_block.get(
                    last.result
                )

                if target:
                    block.add_successor(
                        target
                    )

                    target.add_predecessor(
                        block
                    )

                # Fall-through block
                if index + 1 < len(
                    self.blocks
                ):
                    next_block = self.blocks[
                        index + 1
                    ]

                    block.add_successor(
                        next_block
                    )

                    next_block.add_predecessor(
                        block
                    )

                continue

            # Normal fall-through
            if index + 1 < len(
                self.blocks
            ):

                next_block = self.blocks[
                    index + 1
                ]

                block.add_successor(
                    next_block
                )

                next_block.add_predecessor(
                    block
                )

    # -------------------------
    # Display CFG
    # -------------------------

    def __str__(self):

        if not self.blocks:
            return "<empty CFG>"

        return "\n\n".join(
            str(block)
            for block in self.blocks
        )