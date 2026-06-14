"""Tests for the run_quiet test helper that suppresses optional behaviours."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.mode import Mode


class FakeModelClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        return self._responses.pop(0)


def test_helper_suppresses_summary_by_default(run_quiet):
    fake = FakeModelClient([{"content": "Plain answer.", "tool_calls": None}])
    result = run_quiet("A question.", fake)
    # With the summary suppressed, the result is the bare final answer.
    assert result == "Plain answer."
    assert "Task Summary" not in result


def test_helper_allows_summary_override(run_quiet):
    fake = FakeModelClient([{"content": "Plain answer.", "tool_calls": None}])
    result = run_quiet("A question.", fake, include_summary=True)
    # Overriding re-enables the summary section.
    assert "Task Summary" in result


def test_helper_does_not_classify_by_default(run_quiet):
    # With reading-order declaration suppressed, a single response suffices;
    # if classification ran, it would consume a response and exhaust the list.
    fake = FakeModelClient([{"content": "Answer.", "tool_calls": None}])
    result = run_quiet("Modify something.", fake)
    assert result == "Answer."
    assert fake.calls == 1


def test_helper_passes_session_through(run_quiet, workspace):
    target = workspace / "made.txt"
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "write_file",
                            "arguments": {"path": str(target), "content": "x"},
                        }
                    }
                ],
            },
            {"content": "Done.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_quiet("Write it.", fake, session=session)
    assert result == "Done."
    assert target.read_text() == "x"
