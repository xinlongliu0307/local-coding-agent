"""Operating modes and the approval cadence each one implies."""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    """The agent's operating mode for a task.

    The mode is declared at the start of each task and governs the approval
    cadence used during execution. The names follow the design requirements:
    careful work proceeds step by step, while routine work proceeds with a
    lighter cadence.
    """

    CAREFUL = "careful"
    ROUTINE = "routine"


# Modes that require approval on every individual mutating call. Careful mode
# is used for diagnostic and destructive work, where each mutation warrants a
# separate consent decision.
STEP_BY_STEP_MODES: set[Mode] = {Mode.CAREFUL}


def cadence_for(mode: Mode) -> str:
    """Return a short human-readable description of the approval cadence."""
    if mode in STEP_BY_STEP_MODES:
        return "step-by-step approval on each mutating action"
    return "batched approval once before mutating actions begin"
