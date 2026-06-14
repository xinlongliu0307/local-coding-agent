"""A mutating tool that replaces a unique string within a file.

Matching is exact first. If the exact text is absent, a whitespace-tolerant
fallback looks for the text ignoring differences in spacing, so a model that
does not reproduce the file's exact whitespace can still target the intended
code. The uniqueness safeguard applies to both strategies: a target that
matches more than one place is refused rather than guessed.
"""

from __future__ import annotations

from agent.workspace import resolve_within_workspace, PathOutsideWorkspace


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace a unique occurrence of old_string with new_string in a file.

    This is a mutating tool and must only be invoked after approval. Matching
    is exact first; if the exact text is absent, a whitespace-tolerant
    fallback is tried. In both cases the replacement proceeds only if the
    target matches exactly one place; if it matches none, or more than one,
    the file is left unchanged and an explanatory message is returned.
    """
    try:
        path = resolve_within_workspace(path)
    except PathOutsideWorkspace as error:
        return f"PATH_REFUSED: {error}"

    if not old_string.strip():
        return "No change made: the old_string is empty or only whitespace."

    try:
        with open(path, "r", encoding="utf-8") as handle:
            original = handle.read()
    except OSError as error:
        return f"Error reading '{path}': {error}"

    # Primary strategy: exact matching, unchanged from prior behaviour.
    exact = original.count(old_string)
    if exact == 1:
        return _write(path, original.replace(old_string, new_string),
                      "Replaced one occurrence")
    if exact > 1:
        return (
            f"No change made: the specified text occurs {exact} times "
            f"in '{path}' and is ambiguous. Include more surrounding context "
            "so the target text is unique."
        )

    # Fallback: whitespace-tolerant matching, only when exact finds nothing.
    spans = _whitespace_insensitive_spans(original, old_string)
    if len(spans) == 1:
        start, end = spans[0]
        updated = original[:start] + new_string + original[end:]
        return _write(
            path, updated,
            "Replaced one occurrence (matched ignoring whitespace differences)"
        )
    if len(spans) > 1:
        return (
            f"No change made: ignoring whitespace, the specified text occurs "
            f"{len(spans)} times in '{path}' and is ambiguous. Include more "
            "surrounding context so the target text is unique."
        )

    return (
        f"EDIT_TARGET_NOT_FOUND in '{path}'. The specified text is not "
        "present, even ignoring whitespace. Here are the actual current "
        "contents of the file so you can retry with an exact old_string:"
        f"\n---\n{original}\n---"
    )


def _strip_with_map(text: str) -> tuple[str, list[int]]:
    """Return text with all whitespace removed, plus a map from each kept
    character's stripped index to its original index in text."""
    chars: list[str] = []
    index_map: list[int] = []
    for i, ch in enumerate(text):
        if not ch.isspace():
            chars.append(ch)
            index_map.append(i)
    return "".join(chars), index_map


def _whitespace_insensitive_spans(
    original: str, old_string: str
) -> list[tuple[int, int]]:
    """Return spans in original whose whitespace-removed form equals the
    whitespace-removed old_string. Each span is the minimal slice of original
    covering the matched non-whitespace characters."""
    stripped_original, index_map = _strip_with_map(original)
    stripped_old, _ = _strip_with_map(old_string)
    if not stripped_old:
        return []

    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        pos = stripped_original.find(stripped_old, start)
        if pos == -1:
            break
        end = pos + len(stripped_old)
        spans.append((index_map[pos], index_map[end - 1] + 1))
        start = pos + 1
    return spans


def _write(path: str, updated: str, message: str) -> str:
    """Write updated content to path, returning a success or error message."""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(updated)
    except OSError as error:
        return f"Error writing '{path}': {error}"
    return f"{message} in '{path}'."
