"""A mutating tool that replaces an exact, unique string within a file."""

from __future__ import annotations


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace a unique occurrence of old_string with new_string in a file.

    This is a mutating tool and must only be invoked after approval. The
    replacement proceeds only if old_string occurs exactly once in the file.
    If old_string is absent, or occurs more than once, the file is left
    unchanged and an explanatory message is returned so the agent can adjust
    by supplying more surrounding context to make the target unique.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            original = handle.read()
    except OSError as error:
        return f"Error reading '{path}': {error}"

    occurrences = original.count(old_string)
    if occurrences == 0:
        return (
            f"No change made: the specified text was not found in '{path}'. "
            "Provide the exact existing text, including whitespace."
        )
    if occurrences > 1:
        return (
            f"No change made: the specified text occurs {occurrences} times "
            f"in '{path}' and is ambiguous. Include more surrounding context "
            "so the target text is unique."
        )

    updated = original.replace(old_string, new_string)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(updated)
    except OSError as error:
        return f"Error writing '{path}': {error}"

    return f"Replaced one occurrence in '{path}'."
