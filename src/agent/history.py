"""Bounded conversation history: condense the middle of a long conversation.

The loop appends every message, tool call, and tool result to a single list
that would otherwise grow without bound. When the list grows past a
threshold, the older middle is replaced with a compact digest while the
head (system prompt and original task) and the most recent tail are
preserved verbatim, so the agent can continue on long tasks without the
context window being exhausted.
"""

from __future__ import annotations

from typing import Any


# The conversation is condensed when it grows beyond this many messages.
# The value is deliberately conservative: large enough that short tasks are
# never condensed, small enough to keep long tasks well within context.
DEFAULT_THRESHOLD = 40

# The number of head messages always preserved verbatim: the system prompt
# and the original task message.
HEAD_COUNT = 2

# The number of most-recent messages always preserved verbatim, so the
# agent retains its immediate working context.
TAIL_COUNT = 10


def needs_condensation(
    messages: list[dict[str, Any]], threshold: int = DEFAULT_THRESHOLD
) -> bool:
    """Return True if the message list has grown past the threshold."""
    return len(messages) > threshold


def condense_history(
    messages: list[dict[str, Any]],
    head_count: int = HEAD_COUNT,
    tail_count: int = TAIL_COUNT,
) -> list[dict[str, Any]]:
    """Condense the middle of a conversation, preserving head and tail.

    Returns a new message list consisting of the first head_count messages
    verbatim, a single digest message summarising the condensed middle, and
    the last tail_count messages verbatim. If the list is too short for a
    middle to exist between the head and tail, it is returned unchanged.
    """
    if len(messages) <= head_count + tail_count:
        return list(messages)

    head = messages[:head_count]
    middle = messages[head_count:-tail_count]
    tail = messages[-tail_count:]

    digest = {"role": "user", "content": _digest_middle(middle)}
    return head + [digest] + tail


def _digest_middle(middle: list[dict[str, Any]]) -> str:
    """Produce a compact textual digest of the condensed middle messages."""
    tool_calls = 0
    tool_results = 0
    lines: list[str] = []

    for message in middle:
        role = message.get("role", "")
        if message.get("tool_calls"):
            for call in message["tool_calls"]:
                function = call.get("function", {})
                name = function.get("name", "unknown")
                tool_calls += 1
                lines.append(f"  - called {name}")
        elif role == "tool":
            tool_results += 1
            content = (message.get("content") or "").strip()
            first_line = content.splitlines()[0] if content else ""
            snippet = first_line[:80]
            lines.append(f"  - result: {snippet}")

    summary = [
        "[Earlier conversation condensed to save context. "
        f"{tool_calls} tool call(s) and {tool_results} result(s) occurred:",
    ]
    summary.extend(lines)
    summary.append("End of condensed summary.]")
    return "\n".join(summary)
