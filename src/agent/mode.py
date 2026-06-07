"""Operating modes governing approval cadence and start-of-task clarification."""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    """The agent's operating mode for a task.

    The mode is declared at the start of each task. Careful and routine modes
    govern the approval cadence during execution. Ask mode additionally
    triggers a clarifying-question step before any work begins, for briefs
    that are underspecified at a level where proceeding on assumptions would
    risk producing a structurally wrong result.
    """

    CAREFUL = "careful"
    ROUTINE = "routine"
    ASK = "ask"


# Modes that require approval on every individual mutating call. Ask mode,
# once its clarifying step is satisfied and work proceeds, behaves cautiously
# like careful mode for the remainder of the task.
STEP_BY_STEP_MODES: set[Mode] = {Mode.CAREFUL, Mode.ASK}


# Modes that trigger a clarifying-question step before any work begins.
CLARIFYING_MODES: set[Mode] = {Mode.ASK}


def cadence_for(mode: Mode) -> str:
    """Return a short human-readable description of the approval cadence."""
    if mode in STEP_BY_STEP_MODES:
        return "step-by-step approval on each mutating action"
    return "batched approval once before mutating actions begin"
