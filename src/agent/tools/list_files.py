"""A trivial read-only tool that lists files in a directory."""

from __future__ import annotations

import os


def list_files(directory: str = ".") -> str:
    """Return a newline-separated listing of entries in the given directory.

    This is a read-only tool used to establish the tool interface for the
    agent. It performs no mutation and is safe to call without approval.
    """
    try:
        entries = sorted(os.listdir(directory))
    except OSError as error:
        return f"Error listing '{directory}': {error}"
    return "\n".join(entries) if entries else "(empty directory)"
