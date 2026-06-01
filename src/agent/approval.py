"""The approval gate that governs whether mutating tool calls may proceed."""

from __future__ import annotations

from typing import Any, Callable

from agent.tools.registry import MUTATING_TOOLS


def console_approver(name: str, arguments: dict[str, Any]) -> bool:
    """Ask the user on the console whether a mutating tool call may proceed.

    Presents the tool name and its arguments and waits for a yes or no
    response. Returns True if the user approves, False otherwise. This is the
    default interactive approver used when the agent runs from the command
    line.
    """
    print("\n*** Approval required ***")
    print(f"The agent wants to call the mutating tool: {name}")
    for key, value in arguments.items():
        preview = value if len(str(value)) <= 200 else f"{str(value)[:200]}..."
        print(f"  {key}: {preview}")
    response = input("Approve this action? [y/N] ").strip().lower()
    return response in ("y", "yes")


def is_approved(
    name: str,
    arguments: dict[str, Any],
    approver: Callable[[str, dict[str, Any]], bool],
) -> bool:
    """Decide whether a tool call may proceed.

    Read-only tools are approved automatically. Mutating tools, identified by
    membership in the MUTATING_TOOLS set, are referred to the supplied
    approver function, which decides whether the call is permitted.
    """
    if name not in MUTATING_TOOLS:
        return True
    return approver(name, arguments)
