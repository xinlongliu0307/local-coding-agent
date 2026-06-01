"""Tests for file-manipulation tools and the approval gate."""

from __future__ import annotations

from typing import Any

from agent.approval import is_approved
from agent.loop import run_task
from agent.tools.read_file import read_file
from agent.tools.write_file import write_file


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


def approve_all(name: str, arguments: dict[str, Any]) -> bool:
    return True


def deny_all(name: str, arguments: dict[str, Any]) -> bool:
    return False


def test_write_file_then_read_file_round_trip(tmp_path):
    target = tmp_path / "note.txt"
    write_result = write_file(str(target), "hello world")
    assert "Wrote" in write_result
    assert read_file(str(target)) == "hello world"


def test_read_file_reports_missing_file():
    result = read_file("/path/that/does/not/exist")
    assert "Error" in result


def test_is_approved_passes_read_only_tool_without_asking():
    assert is_approved("read_file", {"path": "x"}, deny_all) is True


def test_is_approved_refers_mutating_tool_to_approver():
    assert is_approved("write_file", {"path": "x", "content": "y"}, deny_all) is False
    assert is_approved("write_file", {"path": "x", "content": "y"}, approve_all) is True


def test_loop_performs_write_when_approved(tmp_path):
    target = tmp_path / "created.txt"
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "write_file",
                            "arguments": {"path": str(target), "content": "data"},
                        }
                    }
                ],
            },
            {"content": "I created the file.", "tool_calls": None},
        ]
    )
    result = run_task(
        "Create the file.", model=fake, approver=approve_all, verbose=False
    )
    assert result == "I created the file."
    assert target.read_text() == "data"


def test_loop_skips_write_when_denied(tmp_path):
    target = tmp_path / "should_not_exist.txt"
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "write_file",
                            "arguments": {"path": str(target), "content": "data"},
                        }
                    }
                ],
            },
            {"content": "I understand, I will not create it.", "tool_calls": None},
        ]
    )
    result = run_task(
        "Create the file.", model=fake, approver=deny_all, verbose=False
    )
    assert result == "I understand, I will not create it."
    assert not target.exists()
