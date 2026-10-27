from difflib import SequenceMatcher

from optimizer.cfg import ControlFlowGraph


def calculate_cfg_statistics(cfg):
    if not isinstance(cfg, ControlFlowGraph):
        raise TypeError(
            f"Expected ControlFlowGraph, got {type(cfg).__name__}"
        )

    instructions = [
        instruction
        for block in cfg.blocks
        for instruction in block.instructions
    ]
    return {
        "block_count": len(cfg.blocks),
        "edge_count": sum(
            len(block.successors)
            for block in cfg.blocks
        ),
        "entry_block_count": sum(
            not block.predecessors
            for block in cfg.blocks
        ),
        "exit_block_count": sum(
            not block.successors
            for block in cfg.blocks
        ),
        "conditional_branch_count": sum(
            bool(block.instructions)
            and block.instructions[-1].operation in {"IF_FALSE", "IF_TRUE"}
            for block in cfg.blocks
        ),
        "label_count": sum(
            instruction.operation == "LABEL"
            for instruction in instructions
        ),
        "maximum_block_size": max(
            (len(block.instructions) for block in cfg.blocks),
            default=0,
        ),
    }


def compare_optimized_instructions(original, optimized):
    original_text = [str(instruction) for instruction in original]
    optimized_text = [str(instruction) for instruction in optimized]
    matcher = SequenceMatcher(
        a=original_text,
        b=optimized_text,
        autojunk=False,
    )

    transformations = []
    changed_indices = []
    instructions_removed = 0

    for tag, original_start, original_end, optimized_start, optimized_end in matcher.get_opcodes():
        if tag == "equal":
            continue

        before = original_text[original_start:original_end]
        after = optimized_text[optimized_start:optimized_end]

        transformations.append({
            "kind": {
                "replace": "changed",
                "delete": "removed",
                "insert": "added",
            }[tag],
            "before": before,
            "after": after,
        })

        if tag == "replace" and len(before) == len(after):
            changed_indices.extend(
                range(optimized_start, optimized_end)
            )

        if tag in {"replace", "delete"}:
            instructions_removed += max(0, len(before) - len(after))

    original_count = len(original_text)
    optimized_count = len(optimized_text)
    reduction_percentage = (
        instructions_removed / original_count * 100
        if original_count
        else 0.0
    )
    statistics = {
        "original_instruction_count": original_count,
        "optimized_instruction_count": optimized_count,
        "instructions_removed": instructions_removed,
        "transformation_count": len(transformations),
        "optimization_percentage": round(reduction_percentage, 1),
    }

    return transformations, changed_indices, statistics
