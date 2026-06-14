"""Detection of unproductive repetition in the agent's loop.

A model operating at the edge of its capability can repeat an action that
just failed, or re-run a check that keeps failing, without recognising it is
making no progress. This module tracks the (call, result) pairs the loop has
seen and reports when one recurs, so the loop can inject a corrective hint
and, if the repetition persists, halt with a clear message rather than
exhausting its iteration limit.

Detection keys on the call AND its result together: re-running a verification
after a genuine change produces a different result and is never flagged; only
a call that produces the identical result it produced before counts as a lack
of progress.
"""

from __future__ import annotations

import json


def call_signature(name: str, arguments) -> str:
    """Return a canonical string identifying a tool call by name and args.

    Arguments may be a dict or an already-serialised string; either is
    rendered to a stable form so the same call always yields the same
    signature regardless of key ordering.
    """
    try:
        args_repr = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        args_repr = repr(arguments)
    return f"{name}::{args_repr}"


class ProgressTracker:
    """Counts identical (call, result) pairs and reports a disposition.

    record() returns one of:
      "ok"   - the pair is new or below the warn threshold;
      "warn" - it has recurred enough to warrant a corrective hint;
      "halt" - it has recurred enough that the loop should stop.
    """

    def __init__(self, warn_at: int = 2, halt_at: int = 3) -> None:
        if warn_at < 2:
            raise ValueError("warn_at must be at least 2")
        if halt_at <= warn_at:
            raise ValueError("halt_at must be greater than warn_at")
        self.warn_at = warn_at
        self.halt_at = halt_at
        self._counts: dict[tuple[str, str], int] = {}

    def record(self, signature: str, result: str) -> str:
        key = (signature, result)
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        if count >= self.halt_at:
            return "halt"
        if count >= self.warn_at:
            return "warn"
        return "ok"

    def repetition_count(self, signature: str, result: str) -> int:
        """Return how many times this (call, result) pair has been recorded."""
        return self._counts.get((signature, result), 0)


def progress_hint() -> str:
    """A corrective notice injected when an action is first seen to repeat."""
    return (
        "PROGRESS_NOTICE: The action you just took produced the same result "
        "as a previous attempt, so it made no progress. Repeating it will not "
        "help. Re-examine the most recent tool results — especially the "
        "actual current contents of any file you are editing — and take a "
        "different action. If the task is already complete or cannot be "
        "completed, say so directly instead of repeating the same step."
    )


def progress_halt_message(result: str, times: int) -> str:
    """The final answer returned when repetition persists past the limit."""
    excerpt = result if len(result) <= 300 else result[:300] + " […]"
    return (
        "The agent stopped because it repeated the same action without making "
        f"progress: the identical result occurred {times} times. This usually "
        "means the model is stuck — for example, repeatedly attempting an edit "
        "whose target text is not present, or re-running a check that keeps "
        "failing without changing the code. The task was not completed. The "
        f"repeated result was:\n{excerpt}"
    )
