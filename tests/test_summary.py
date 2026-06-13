"""Tests for the task record and the end-of-task self-summary."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode
from agent.record import TaskRecord
from agent.summary import build_summary


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


def _write_call(path: str, content: str) -> dict[str, Any]:
    return {
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "write_file",
                    "arguments": {"path": path, "content": content},
                }
            }
        ],
    }


def test_record_classifies_created_file(workspace):
    target = workspace / "new.txt"
    record = TaskRecord()
    existed = record.note_pre_state("write_file", {"path": str(target)})
    record.add_event(
        "write_file",
        {"path": str(target)},
        approved=True,
        result="Wrote 1 characters.",
        existed_before=existed,
    )
    assert str(target) in record.created_files
    assert str(target) not in record.modified_files


def test_record_classifies_modified_file(workspace):
    target = workspace / "existing.txt"
    target.write_text("original")
    record = TaskRecord()
    existed = record.note_pre_state("write_file", {"path": str(target)})
    record.add_event(
        "write_file",
        {"path": str(target)},
        approved=True,
        result="Wrote 1 characters.",
        existed_before=existed,
    )
    assert str(target) in record.modified_files
    assert str(target) not in record.created_files


def test_record_notes_declined_action():
    record = TaskRecord()
    record.add_event(
        "write_file",
        {"path": "x"},
        approved=False,
        result="declined",
        existed_before=False,
    )
    assert "write_file" in record.declined_actions
    assert record.created_files == []


def test_summary_reports_created_and_modified_sections():
    record = TaskRecord()
    record.created_files.append("a.txt")
    record.modified_files.append("b.txt")
    summary = build_summary(record)
    assert "Files created:" in summary
    assert "a.txt" in summary
    assert "Files modified:" in summary
    assert "b.txt" in summary


def test_summary_reports_none_for_empty_categories():
    summary = build_summary(TaskRecord())
    assert "Files created: none" in summary
    assert "Files modified: none" in summary
    assert "Actions declined by the user: none" in summary


def test_loop_appends_summary_reflecting_created_file(workspace):
    target = workspace / "made.txt"
    fake = FakeModelClient(
        [
            _write_call(str(target), "data"),
            {"content": "Done.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_task(
        "Create a file.",
        model=fake,
        session=session,
        verbose=False,
        declare_reading_order=False,
    )
    assert "Done." in result
    assert "Task Summary" in result
    assert str(target) in result
    assert target.read_text() == "data"
