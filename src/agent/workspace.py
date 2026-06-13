"""Workspace confinement: keep file operations inside a permitted root.

The file tools must not operate on arbitrary paths. Each tool resolves the
path it is given against a workspace root and refuses any path that resolves
outside it, after symlinks and parent-directory traversal are accounted for.
This confines the agent to a scoped directory even if the model supplies a
path — hallucinated, traversing, or symlinked — that points elsewhere.
"""

from __future__ import annotations

import os


class PathOutsideWorkspace(Exception):
    """Raised when a path resolves outside the permitted workspace root."""


# The active workspace root. None means "use the current working directory
# at call time", which preserves behaviour for tasks run from within a
# project while still applying the containment boundary.
_active_root: str | None = None


def set_workspace_root(root: str | None) -> None:
    """Set the active workspace root, or None to use the working directory."""
    global _active_root
    _active_root = root


def get_workspace_root() -> str:
    """Return the active workspace root, resolved to a canonical path."""
    root = _active_root if _active_root is not None else os.getcwd()
    return os.path.realpath(root)


def resolve_within_workspace(path: str, root: str | None = None) -> str:
    """Resolve a path and confirm it lies within the workspace root.

    Returns the canonical, symlink-free absolute path if it is the root
    itself or a descendant of it. Raises PathOutsideWorkspace otherwise.
    The candidate is resolved before comparison so that '..' traversal and
    symlinks cannot escape the root.
    """
    base = os.path.realpath(root) if root is not None else get_workspace_root()

    candidate = path if os.path.isabs(path) else os.path.join(base, path)
    resolved = os.path.realpath(candidate)

    # Contained if it is the root itself or sits beneath root + separator.
    if resolved == base or resolved.startswith(base + os.sep):
        return resolved

    raise PathOutsideWorkspace(
        f"path '{path}' resolves outside the workspace root '{base}'"
    )
