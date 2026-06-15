"""A mutating tool that replaces a unique string within a file.

Matching is exact first. If the exact text is absent, a whitespace-tolerant
fallback looks for the text ignoring differences in spacing. The fallback is
restricted to single-line, in-line replacements: whitespace in multi-line
code is the block structure, so a whitespace-insensitive match is only
meaningful within one line. Any multi-line case defers to exact matching,
which correctly requires the indentation to be reproduced. The uniqueness
safeguard applies to both strategies: a target that matches more than one
place is refused rather than guessed.
"""

from __future__ import annotations

from agent.workspace import resolve_within_workspace, PathOutsideWorkspace


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace a unique occurrence of old_string with new_string in a file.

    This is a mutating tool and must only be invoked after approval. Matching
    is exact first; if the exact text is absent, a single-line whitespace-
    tolerant fallback is tried. In both cases the replacement proceeds only if
    the target matches exactly one place; if it matches none, or more than
    one, the file is left unchanged and an explanatory message is returned.
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
    # Restricted to single-line, in-line replacements. The fallback engages
    # only when the new_string is itself single-line, and only spans lying
    # within one line are considered (see _whitespace_insensitive_spans).
    # Splicing across a line break would corrupt indentation, so any
    # multi-line case falls through to EDIT_TARGET_NOT_FOUND, which sends the
    # file contents back so the model can retry with an exact, correctly
    # indented old_string.
    if "\n" not in new_string:
        spans = _whitespace_insensitive_spans(original, old_string)
        if len(spans) == 1:
            start, end = spans[0]
            updated = original[:start] + new_string + original[end:]
            return _write(
                path, updated,
                "Replaced one occurrence (matched ignoring whitespace "
                "differences)"
            )
        if len(spans) > 1:
            return (
                f"No change made: ignoring whitespace, the specified text "
                f"occurs {len(spans)} times in '{path}' and is ambiguous. "
                "Include more surrounding context so the target is unique."
            )

    return (
        f"EDIT_TARGET_NOT_FOUND in '{path}'. The specified text is not "
        "present as an exact match, and no safe single-line whitespace-"
        "tolerant match was found. Here are the actual current contents of "
        "the file so you can retry with an exact old_string that reproduces "
        f"the indentation:\n---\n{original}\n---"
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
    covering the matched non-whitespace characters. Spans that cross a line
    break are excluded, so only matches lying within a single line are
    returned; this keeps the whitespace-tolerant replacement from splicing
    across lines and corrupting indentation."""
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
        span_start = index_map[pos]
        span_end = index_map[end - 1] + 1
        if "\n" not in original[span_start:span_end]:
            spans.append((span_start, span_end))
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
