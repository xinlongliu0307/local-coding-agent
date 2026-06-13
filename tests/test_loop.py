"""Tests for the ReAct loop, using a scripted fake model client."""

from __future__ import annotations

from typing import Any

from agent.loop import run_task

from agent.approval import ApprovalSession
from agent.mode import Mode


class FakeModelClient:
    """A model client that returns a predetermined sequence of responses."""

    def __init__(self, scripted_responses: list[dict[str, Any]]) -> None:
        self._responses = list(scripted_responses)
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        return self._responses.pop(0)


def test_loop_returns_text_when_no_tool_called():
    fake = FakeModelClient(
        [
            {"content": "The answer is 42.", "tool_calls": None},
        ]
    )
    result = run_task(
        "What is the answer?",
        model=fake,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "The answer is 42."
    assert fake.calls == 1


def test_loop_executes_tool_then_returns_final_answer():
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "list_files",
                            "arguments": {"directory": "."},
                        }
                    }
                ],
            },
            {"content": "I listed the files.", "tool_calls": None},
        ]
    )
    result = run_task(
        "List the files.",
        model=fake,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "I listed the files."
    assert fake.calls == 2


def test_loop_handles_unknown_tool_gracefully():
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "nonexistent_tool", "arguments": {}}}
                ],
            },
            {"content": "I could not use that tool.", "tool_calls": None},
        ]
    )
    result = run_task(
        "Do something impossible.",
        model=fake,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "I could not use that tool."
    assert fake.calls == 2


def test_loop_detects_tool_call_embedded_in_content():
    fake = FakeModelClient(
        [
            {
                "content": '{"name": "list_files", "arguments": {"directory": "."}}',
                "tool_calls": None,
            },
            {"content": "I listed the files.", "tool_calls": None},
        ]
    )
    result = run_task(
        "List the files.",
        model=fake,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "I listed the files."
    assert fake.calls == 2


def test_loop_detects_multiple_tool_calls_embedded_in_content(workspace):
    file_a = workspace / "a.txt"
    file_b = workspace / "b.txt"
    content = (
        f'{{"name": "write_file", "arguments": {{"path": "{file_a}", '
        f'"content": "a"}}}}\n'
        f'{{"name": "write_file", "arguments": {{"path": "{file_b}", '
        f'"content": "b"}}}}'
    )
    fake = FakeModelClient(
        [
            {"content": content, "tool_calls": None},
            {"content": "Both files created.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_task(
        "Create two files.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "Both files created."
    assert file_a.read_text() == "a"
    assert file_b.read_text() == "b"
