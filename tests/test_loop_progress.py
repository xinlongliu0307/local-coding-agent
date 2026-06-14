"""Tests that the loop detects and responds to unproductive repetition."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.mode import Mode


class RecordingClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls = 0
        self.last_messages: list[dict[str, Any]] = []

    def chat(self, messages, tools=None):
        self.calls += 1
        self.last_messages = list(messages)
        return self._responses.pop(0)


def _failing_edit(target):
    return {
        "content": "",
        "tool_calls": [
            {"function": {"name": "edit_file",
                          "arguments": {"path": str(target),
                                        "old_string": "not present",
                                        "new_string": "y"}}}
        ],
    }


def test_loop_halts_on_repeated_failing_edit(workspace, run_quiet):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    fail = _failing_edit(target)
    client = RecordingClient(
        [fail, fail, fail, {"content": "unreached", "tool_calls": None}]
    )
    session = ApprovalSession(Mode.ROUTINE, lambda n, a: True, lambda: True)
    result = run_quiet("Edit it.", client, session=session,
                       enable_progress_detection=True)
    assert "without making progress" in result
    assert client.calls == 3


def test_loop_injects_notice_on_second_repeat(workspace, run_quiet):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    fail = _failing_edit(target)
    client = RecordingClient(
        [fail, fail, fail, {"content": "unreached", "tool_calls": None}]
    )
    session = ApprovalSession(Mode.ROUTINE, lambda n, a: True, lambda: True)
    run_quiet("Edit it.", client, session=session,
              enable_progress_detection=True)
    # By the third model call, the corrective notice must be in the context.
    assert any(
        m.get("role") == "user" and "PROGRESS_NOTICE" in m.get("content", "")
        for m in client.last_messages
    )


def test_loop_does_not_halt_without_repetition(workspace, run_quiet):
    target = workspace / "code.py"
    target.write_text("greeting = 'hi'\n")
    client = RecordingClient([
        {"content": "", "tool_calls": [
            {"function": {"name": "edit_file",
                          "arguments": {"path": str(target),
                                        "old_string": "greeting = 'hi'",
                                        "new_string": "greeting = 'hello'"}}}]},
        {"content": "Done.", "tool_calls": None},
    ])
    session = ApprovalSession(Mode.ROUTINE, lambda n, a: True, lambda: True)
    result = run_quiet("Edit it.", client, session=session,
                       enable_progress_detection=True)
    assert result == "Done."
    assert target.read_text() == "greeting = 'hello'\n"
