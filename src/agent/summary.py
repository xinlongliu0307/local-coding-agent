"""Construction of the end-of-task self-summary from a task record."""

from __future__ import annotations

from agent.record import TaskRecord


def build_summary(record: TaskRecord) -> str:
    """Construct a structured self-summary from a completed task record.

    The summary enumerates, in separate sections, the files created and
    modified, the tools invoked with their outcomes, and any actions the
    user declined. It is built deterministically from the record rather than
    from the model's recollection, so that the account is factual.
    """
    lines: list[str] = ["", "=== Task Summary ==="]

    if record.created_files:
        lines.append("Files created:")
        for path in record.created_files:
            lines.append(f"  - {path}")
    else:
        lines.append("Files created: none")

    if record.modified_files:
        lines.append("Files modified:")
        for path in record.modified_files:
            lines.append(f"  - {path}")
    else:
        lines.append("Files modified: none")

    mutating_events = [event for event in record.events if event.mutating]
    read_events = [event for event in record.events if not event.mutating]
    lines.append(
        f"Tools invoked: {len(record.events)} total "
        f"({len(mutating_events)} mutating, {len(read_events)} read-only)"
    )

    if record.declined_actions:
        lines.append("Actions declined by the user:")
        for name in record.declined_actions:
            lines.append(f"  - {name}")
    else:
        lines.append("Actions declined by the user: none")

    return "\n".join(lines)
