"""A read-only tool that returns the contents of a file."""

from __future__ import annotations


def read_file(path: str) -> str:
    """Return the contents of the file at the given path.

    This is a read-only tool and is safe to call without approval. If the
    file cannot be read, an error string is returned so that the agent can
    observe the failure rather than the loop crashing.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        return f"Error reading '{path}': {error}"
