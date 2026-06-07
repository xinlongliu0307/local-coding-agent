"""Task-type classification and the reading order each type implies."""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Any

from agent.model import ModelClient


class TaskType(str, Enum):
    """The kind of task, which determines the reading order to declare."""

    MODIFICATION = "modification"
    DIAGNOSTIC = "diagnostic"
    OTHER = "other"


# The reading order associated with each task type, expressed as an ordered
# list of stages. Modification work reads from the public surface inward;
# diagnostic work reads along the execution pipeline.
READING_ORDERS: dict[TaskType, list[str]] = {
    TaskType.MODIFICATION: [
        "public interface",
        "test contract",
        "implementation",
        "build configuration",
        "entry point",
    ],
    TaskType.DIAGNOSTIC: [
        "entry point",
        "suspected calculation",
        "data loading",
        "tests",
        "configuration",
    ],
}


CLASSIFY_SYSTEM_PROMPT = (
    "You classify a software task into one of three types. Respond "
    "'modification' if the task changes existing code, such as refactoring, "
    "renaming, or altering behaviour. Respond 'diagnostic' if the task is to "
    "find and fix a bug or explain wrong behaviour in existing code. Respond "
    "'other' if the task creates something new or does not involve reading "
    "existing code. Respond strictly as JSON of the form "
    '{"task_type": "modification"} with no other text.'
)


def classify_task(task: str, model: ModelClient) -> TaskType:
    """Classify a task brief into a task type using the model.

    Returns one of the TaskType values. If the model's response cannot be
    parsed or names an unrecognised type, the task is conservatively
    classified as OTHER, so that no reading-order declaration is made for a
    task whose type could not be determined.
    """
    messages = [
        {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    raw = model.chat(messages)
    content = raw.get("content", "") if isinstance(raw, dict) else ""

    parsed = _parse_classification(content)
    if parsed is None:
        return TaskType.OTHER

    value = parsed.get("task_type", "")
    if not isinstance(value, str):
        return TaskType.OTHER
    try:
        return TaskType(value.strip().lower())
    except ValueError:
        return TaskType.OTHER


def reading_order_declaration(task_type: TaskType) -> str | None:
    """Return a declared reading-order statement for a task type.

    Returns a human-readable sentence naming the order in which existing code
    will be read, or None for the OTHER type, which has no associated order.
    """
    order = READING_ORDERS.get(task_type)
    if not order:
        return None
    sequence = ", then ".join(order)
    return (
        f"This is a {task_type.value} task. I will read existing code in "
        f"this order: {sequence}."
    )


def _parse_classification(content: str) -> dict[str, Any] | None:
    """Parse the model's JSON classification, tolerating surrounding text."""
    if not content:
        return None
    candidate = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if match:
            candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
