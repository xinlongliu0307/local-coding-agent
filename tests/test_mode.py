"""Tests for the three-mode disposition and the approval cadence."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode, cadence_for


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


class CountingApprover:
    """A per-call approver that counts how many times it is consulted."""

    def __init__(self, decision: bool) -> None:
        self.decision = decision
        self.calls = 0

    def __call__(self, name: str, arguments: dict[str, Any]) -> bool:
        self.calls += 1
        return self.decision


class CountingBatchApprover:
    """A batch approver that counts how many times it is consulted."""

    def __init__(self, decision: bool) -> None:
        self.decision = decision
        self.calls = 0

    def __call__(self) -> bool:
        self.calls += 1
        return self.decision


def _two_write_then_finish(path_a: str, path_b: str) -> list[dict[str, Any]]:
    return [
        {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": {"path": path_a, "content": "a"},
                    }
                }
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": {"path": path_b, "content": "b"},
                    }
                }
            ],
        },
        {"content": "Both files created.", "tool_calls": None},
    ]


def test_cadence_description_differs_by_mode():
    assert "step-by-step" in cadence_for(Mode.CAREFUL)
    assert "batched" in cadence_for(Mode.ROUTINE)


def test_careful_mode_asks_on_every_mutating_call(workspace):
    file_a = workspace / "a.txt"
    file_b = workspace / "b.txt"
    per_call = CountingApprover(decision=True)
    batch = CountingBatchApprover(decision=True)
    session = ApprovalSession(Mode.CAREFUL, per_call, batch)
    fake = FakeModelClient(_two_write_then_finish(str(file_a), str(file_b)))

    result = run_task(
        "Create two files.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )

    assert result == "Both files created."
    assert per_call.calls == 2
    assert batch.calls == 0
    assert file_a.read_text() == "a"
    assert file_b.read_text() == "b"


def test_routine_mode_asks_once_for_multiple_mutations(workspace):
    file_a = workspace / "a.txt"
    file_b = workspace / "b.txt"
    per_call = CountingApprover(decision=True)
    batch = CountingBatchApprover(decision=True)
    session = ApprovalSession(Mode.ROUTINE, per_call, batch)
    fake = FakeModelClient(_two_write_then_finish(str(file_a), str(file_b)))

    result = run_task(
        "Create two files.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )

    assert result == "Both files created."
    assert batch.calls == 1
    assert per_call.calls == 0
    assert file_a.read_text() == "a"
    assert file_b.read_text() == "b"


def test_routine_mode_denial_blocks_all_mutations(workspace):
    file_a = workspace / "a.txt"
    file_b = workspace / "b.txt"
    per_call = CountingApprover(decision=True)
    batch = CountingBatchApprover(decision=False)
    session = ApprovalSession(Mode.ROUTINE, per_call, batch)
    fake = FakeModelClient(_two_write_then_finish(str(file_a), str(file_b)))

    result = run_task(
        "Create two files.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )

    assert result == "Both files created."
    assert batch.calls == 1
    assert not file_a.exists()
    assert not file_b.exists()
