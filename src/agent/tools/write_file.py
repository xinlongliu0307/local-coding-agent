"""A mutating tool that writes content to a file, creating or overwriting it."""

from __future__ import annotations

import os


def write_file(path: str, content: str) -> str:
    """Write the given content to the file at the given path.

    This is a mutating tool: it creates the file if it does not exist and
    overwrites it if it does. It must only be invoked after approval. Any
    parent directories in the path are created as needed. Returns a short
    confirmation describing what was written, or an error string on failure.
    """
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return f"Wrote {len(content)} characters to '{path}'."
    except OSError as error:
        return f"Error writing '{path}': {error}"
