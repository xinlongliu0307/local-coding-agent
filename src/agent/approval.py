"""The approval gate and the session state that governs approval cadence."""

from __future__ import annotations

from typing import Any, Callable

from agent.mode import Mode, STEP_BY_STEP_MODES
from agent.tools.registry import MUTATING_TOOLS
from agent.command_policy import classify_command, Disposition


def console_approver(name: str, arguments: dict[str, Any]) -> bool:
    """Ask the user on the console whether a mutating tool call may proceed."""
    print("\n*** Approval required ***")
    print(f"The agent wants to call the mutating tool: {name}")
    for key, value in arguments.items():
        preview = value if len(str(value)) <= 200 else f"{str(value)[:200]}..."
        print(f"  {key}: {preview}")
    if name == "run_command":
        disposition = classify_command(arguments.get("command", ""))
        if disposition is Disposition.UNRECOGNISED:
            print(
                "  \u26a0 This command is not on the recognised-safe list. "
                "Review it carefully before approving."
            )
    response = input("Approve this action? [y/N] ").strip().lower()
    return response in ("y", "yes")


def batch_console_approver() -> bool:
    """Ask the user once whether mutating actions may proceed for the task."""
    print("\n*** Batch approval required ***")
    print(
        "This task is running in routine mode. The agent may perform multiple "
        "mutating actions. Approving once permits all mutating actions for "
        "this task."
    )
    response = input("Approve mutating actions for this task? [y/N] ").strip().lower()
    return response in ("y", "yes")


class ApprovalSession:
    """Tracks approval state across the tool calls of a single task.

    In a step-by-step mode, every mutating call is referred to the per-call
    approver. In a batched mode, the first mutating call triggers a single
    batch approval that is remembered and applied to all subsequent mutating
    calls within the same task.
    """

    def __init__(
        self,
        mode: Mode,
        per_call_approver: Callable[[str, dict[str, Any]], bool],
        batch_approver: Callable[[], bool],
    ) -> None:
        self.mode = mode
        self._per_call_approver = per_call_approver
        self._batch_approver = batch_approver
        self._batch_decision: bool | None = None

    def is_approved(self, name: str, arguments: dict[str, Any]) -> bool:
        """Decide whether a tool call may proceed under the session's cadence."""
        if name not in MUTATING_TOOLS:
            return True

        if self.mode in STEP_BY_STEP_MODES:
            return self._per_call_approver(name, arguments)

        # Batched cadence: decide once, then reuse the decision.
        if self._batch_decision is None:
            self._batch_decision = self._batch_approver()
        return self._batch_decision
