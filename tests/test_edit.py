"""Tests for the targeted file-editing tool and its approval gating."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode
from agent.tools.edit_file import edit_file


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


def test_edit_replaces_unique_occurrence(workspace):
    target = workspace / "code.py"
    target.write_text("x = 1\ny = 2\nz = 3\n")
    result = edit_file(str(target), "y = 2", "y = 20")
    assert "Replaced one occurrence" in result
    assert target.read_text() == "x = 1\ny = 20\nz = 3\n"


def test_edit_refuses_when_target_absent(workspace):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    result = edit_file(str(target), "not present", "replacement")
    assert "EDIT_TARGET_NOT_FOUND" in result
    assert target.read_text() == "x = 1\n"


def test_edit_refuses_when_target_ambiguous(workspace):
    target = workspace / "code.py"
    target.write_text("value = 1\nvalue = 1\n")
    result = edit_file(str(target), "value = 1", "value = 2")
    assert "ambiguous" in result
    assert target.read_text() == "value = 1\nvalue = 1\n"


def test_edit_reports_missing_file(workspace):
    result = edit_file(str(workspace / "does_not_exist.py"), "a", "b")
    assert "Error" in result


def test_loop_performs_edit_when_approved(workspace):
    target = workspace / "code.py"
    target.write_text("greeting = 'hello'\n")
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "edit_file",
                            "arguments": {
                                "path": str(target),
                                "old_string": "greeting = 'hello'",
                                "new_string": "greeting = 'goodbye'",
                            },
                        }
                    }
                ],
            },
            {"content": "I updated the greeting.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_task(
        "Update the greeting.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "I updated the greeting."
    assert target.read_text() == "greeting = 'goodbye'\n"


def test_loop_skips_edit_when_denied(workspace):
    target = workspace / "code.py"
    target.write_text("greeting = 'hello'\n")
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "edit_file",
                            "arguments": {
                                "path": str(target),
                                "old_string": "greeting = 'hello'",
                                "new_string": "greeting = 'goodbye'",
                            },
                        }
                    }
                ],
            },
            {"content": "I left the file unchanged.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: False, lambda: False)
    result = run_task(
        "Update the greeting.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "I left the file unchanged."
    assert target.read_text() == "greeting = 'hello'\n"
