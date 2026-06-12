"""Tests for bounded conversation-history condensation."""

from __future__ import annotations

from typing import Any

from agent.history import (
    DEFAULT_THRESHOLD,
    HEAD_COUNT,
    TAIL_COUNT,
    condense_history,
    needs_condensation,
)


def _message(role: str, content: str = "") -> dict[str, Any]:
    return {"role": role, "content": content}


def _tool_call_message(name: str) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": name, "arguments": {}}}],
    }


def test_needs_condensation_false_below_threshold():
    messages = [_message("user") for _ in range(DEFAULT_THRESHOLD)]
    assert needs_condensation(messages) is False


def test_needs_condensation_true_above_threshold():
    messages = [_message("user") for _ in range(DEFAULT_THRESHOLD + 1)]
    assert needs_condensation(messages) is True


def test_condense_returns_unchanged_when_short():
    messages = [_message("system"), _message("user"), _message("assistant")]
    assert condense_history(messages) == messages


def test_condense_preserves_head_and_tail_counts():
    messages = [_message("system"), _message("user")]
    messages += [_tool_call_message("read_file") for _ in range(30)]
    messages += [_message("assistant", f"recent {i}") for i in range(TAIL_COUNT)]

    condensed = condense_history(messages)

    # Head preserved verbatim.
    assert condensed[:HEAD_COUNT] == messages[:HEAD_COUNT]
    # Tail preserved verbatim.
    assert condensed[-TAIL_COUNT:] == messages[-TAIL_COUNT:]
    # Exactly one digest message sits between head and tail.
    assert len(condensed) == HEAD_COUNT + 1 + TAIL_COUNT


def test_condense_digest_mentions_tool_activity():
    messages = [_message("system"), _message("user")]
    messages += [_tool_call_message("read_file") for _ in range(20)]
    messages += [_message("tool", "some result") for _ in range(5)]
    messages += [_message("assistant", f"recent {i}") for i in range(TAIL_COUNT)]

    condensed = condense_history(messages)
    digest = condensed[HEAD_COUNT]["content"]

    assert "condensed" in digest.lower()
    assert "read_file" in digest


def test_condense_digest_is_in_user_role():
    messages = [_message("system"), _message("user")]
    messages += [_tool_call_message("write_file") for _ in range(30)]
    messages += [_message("assistant", f"recent {i}") for i in range(TAIL_COUNT)]

    condensed = condense_history(messages)
    assert condensed[HEAD_COUNT]["role"] == "user"
