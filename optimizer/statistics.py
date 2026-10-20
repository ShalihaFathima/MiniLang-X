from difflib import SequenceMatcher


def calculate_cfg_statistics(cfg):
    blocks = cfg.blocks

    return {
        "block_count": len(blocks),
        "edge_count": sum(len(block.successors) for block in blocks),
        "entry_block_count": 1 if blocks else 0,
        "exit_block_count": sum(not block.successors for block in blocks),
        "conditional_branch_count": sum(
            bool(block.instructions)
            and block.instructions[-1].operation in {"IF_FALSE", "IF_TRUE"}
            for block in blocks
        ),
        "label_count": sum(
            instruction.operation == "LABEL"
            for block in blocks
            for instruction in block.instructions
        ),
        "maximum_block_size": max(
            (len(block.instructions) for block in blocks),
            default=0,
        ),
    }


def compare_optimized_instructions(original, optimized):
    """
    Compare original and optimized TAC as sequences (difflib), so an
    instruction that only moved because earlier ones were removed is
    not reported as changed.

    Returns (transformations, changed_indices, statistics):

      transformations   one entry per differing segment:
                        {"kind": "changed" | "removed" | "added",
                         "before": [...], "after": [...],
                         "original_start": i, "optimized_start": j}
      changed_indices   positions in the optimized TAC that replaced an
                        original instruction one-for-one
      statistics        instruction counts and reduction percentage
    """
    before_text = [str(instruction) for instruction in original]
    after_text = [str(instruction) for instruction in optimized]

    kinds = {"replace": "changed", "delete": "removed", "insert": "added"}

    transformations = []
    changed_indices = []

    matcher = SequenceMatcher(a=before_text, b=after_text, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        transformations.append({
            "kind": kinds[tag],
            "before": before_text[i1:i2],
            "after": after_text[j1:j2],
            "original_start": i1,
            "optimized_start": j1,
        })

        # Only a same-length replacement maps instructions one-to-one
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            changed_indices.extend(range(j1, j2))

    original_count = len(before_text)
    optimized_count = len(after_text)
    removed = original_count - optimized_count

    return transformations, changed_indices, {
        "original_instruction_count": original_count,
        "optimized_instruction_count": optimized_count,
        "instructions_removed": removed,
        "transformation_count": len(transformations),
        "optimization_percentage": (
            round(removed / original_count * 100, 1)
            if original_count
            else 0.0
        ),
    }
