"""A read-only tool that searches file contents for a literal string."""

from __future__ import annotations

import os


MAX_RESULTS = 50
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def search_files(query: str, directory: str = ".") -> str:
    """Search files under a directory for a literal substring.

    Returns matching locations as 'path:line: text' lines, capped at a
    maximum number of results. Hidden tooling directories are skipped.
    Binary or unreadable files are silently ignored. Read-only and safe.
    """
    if not query:
        return "Error: an empty search query is not allowed."

    matches: list[str] = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    for number, line in enumerate(handle, start=1):
                        if query in line:
                            matches.append(
                                f"{path}:{number}: {line.rstrip()}"
                            )
                            if len(matches) >= MAX_RESULTS:
                                matches.append(
                                    f"(stopped after {MAX_RESULTS} matches)"
                                )
                                return "\n".join(matches)
            except (OSError, UnicodeDecodeError):
                continue

    if not matches:
        return f"No matches found for '{query}' under '{directory}'."
    return "\n".join(matches)
