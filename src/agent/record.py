"""A record of events during a task, used to construct the self-summary."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from agent.tools.registry import MUTATING_TOOLS


@dataclass
class ToolEvent:
    """A single tool invocation and its outcome during a task."""

    name: str
    arguments: dict[str, Any]
    approved: bool
    result: str
    mutating: bool


@dataclass
class TaskRecord:
    """An accumulating record of everything that happened during a task.

    The loop appends a ToolEvent for each tool the model requests. The record
    distinguishes mutating from read-only tools and, for file-writing tools,
    notes whether the target existed before the operation so that created and
    modified files can be reported separately.
    """

    events: list[ToolEvent] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    declined_actions: list[str] = field(default_factory=list)

    def note_pre_state(self, name: str, arguments: dict[str, Any]) -> bool:
        """Record whether a file target exists before a write, for later use.

        Returns True if the operation targets a path that already exists,
        indicating a modification rather than a creation. Called before the
        tool runs so that the prior state is captured accurately.
        """
        path = arguments.get("path")
        if not isinstance(path, str):
            return False
        return os.path.exists(path)

    def add_event(
        self,
        name: str,
        arguments: dict[str, Any],
        approved: bool,
        result: str,
        existed_before: bool,
    ) -> None:
        """Append a tool event and update the file classification lists."""
        mutating = name in MUTATING_TOOLS
        self.events.append(
            ToolEvent(
                name=name,
                arguments=arguments,
                approved=approved,
                result=result,
                mutating=mutating,
            )
        )

        if not approved:
            self.declined_actions.append(name)
            return

        path = arguments.get("path")
        if mutating and isinstance(path, str) and "Error" not in result:
            if existed_before:
                if path not in self.modified_files:
                    self.modified_files.append(path)
            else:
                if path not in self.created_files:
                    self.created_files.append(path)
