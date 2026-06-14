"""Tests for unproductive-repetition detection."""

from __future__ import annotations

import pytest

from agent.progress import (
    ProgressTracker,
    call_signature,
    progress_hint,
    progress_halt_message,
)


def test_signature_is_stable_regardless_of_arg_order():
    a = call_signature("edit_file",
                       {"path": "f", "old_string": "x", "new_string": "y"})
    b = call_signature("edit_file",
                       {"new_string": "y", "old_string": "x", "path": "f"})
    assert a == b


def test_distinct_calls_have_distinct_signatures():
    a = call_signature("edit_file", {"path": "f", "old_string": "x"})
    b = call_signature("edit_file", {"path": "g", "old_string": "x"})
    assert a != b


def test_first_occurrence_is_ok():
    assert ProgressTracker().record("sig", "result") == "ok"


def test_second_identical_pair_warns():
    tracker = ProgressTracker()
    tracker.record("sig", "result")
    assert tracker.record("sig", "result") == "warn"


def test_third_identical_pair_halts():
    tracker = ProgressTracker()
    tracker.record("sig", "result")
    tracker.record("sig", "result")
    assert tracker.record("sig", "result") == "halt"


def test_same_call_different_result_does_not_trigger():
    tracker = ProgressTracker()
    assert tracker.record("run_command::check", "FAIL") == "ok"
    assert tracker.record("run_command::check", "PASS") == "ok"


def test_different_calls_do_not_accumulate_together():
    tracker = ProgressTracker()
    assert tracker.record("sig_a", "r") == "ok"
    assert tracker.record("sig_b", "r") == "ok"
    assert tracker.record("sig_a", "r") == "warn"


def test_invalid_thresholds_are_rejected():
    with pytest.raises(ValueError):
        ProgressTracker(warn_at=1)
    with pytest.raises(ValueError):
        ProgressTracker(warn_at=3, halt_at=3)


def test_hint_and_halt_messages_carry_expected_text():
    assert "PROGRESS_NOTICE" in progress_hint()
    msg = progress_halt_message("some result", 3)
    assert "stopped" in msg
    assert "3 times" in msg


def test_halt_message_truncates_long_results():
    msg = progress_halt_message("x" * 1000, 3)
    assert "[…]" in msg
    assert len(msg) < 1000
