"""Tests for whitespace-tolerant fallback matching in edit_file."""

from __future__ import annotations

from agent.tools.edit_file import edit_file


def test_exact_match_still_works(workspace):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    result = edit_file(str(target), "x = 1", "x = 2")
    assert "Replaced one occurrence" in result
    assert "ignoring whitespace" not in result
    assert target.read_text() == "x = 2\n"


def test_whitespace_difference_is_bridged(workspace):
    target = workspace / "code.py"
    # The file spaces the operator; the old_string is compact.
    target.write_text("result = a + b\n")
    result = edit_file(str(target), "a+b", "a - b")
    assert "Replaced one occurrence" in result
    assert "ignoring whitespace" in result
    assert target.read_text() == "result = a - b\n"


def test_multiline_spacing_is_bridged(workspace):
    target = workspace / "code.py"
    target.write_text("def f():\n    return  x  +  y\n")
    # old_string with single spaces; the file uses double spaces.
    result = edit_file(str(target), "return x + y", "return x - y")
    assert "Replaced one occurrence" in result
    assert "return x - y" in target.read_text()


def test_fallback_preserves_uniqueness(workspace):
    target = workspace / "code.py"
    # Two whitespace variants of the same content; a compact old_string
    # matching neither exactly must be refused as ambiguous under fallback.
    target.write_text("a + b\na+b\n")
    result = edit_file(str(target), "a  +  b", "X")
    assert "ambiguous" in result
    assert target.read_text() == "a + b\na+b\n"


def test_not_found_even_ignoring_whitespace(workspace):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    result = edit_file(str(target), "nonexistent", "y")
    assert "EDIT_TARGET_NOT_FOUND" in result
    assert target.read_text() == "x = 1\n"


def test_empty_old_string_refused(workspace):
    target = workspace / "code.py"
    target.write_text("x = 1\n")
    result = edit_file(str(target), "   ", "y")
    assert "No change made" in result
    assert target.read_text() == "x = 1\n"


def test_multiline_edit_refuses_whitespace_fallback(workspace):
    # Reproduces the meteorological trial: an old_string that matches ignoring
    # whitespace but spans two lines, with a multi-line new_string. The
    # fallback must NOT apply, because splicing across lines corrupts
    # indentation. The file must be left untouched.
    target = workspace / "code.py"
    target.write_text(
        "def f(x):\n"
        "    # y = x + 1\n"
        "    return x + 1\n"
    )
    result = edit_file(
        str(target),
        "# y = x + 1\nreturn x + 1",
        "y = x + 1\nreturn y",
    )
    assert "EDIT_TARGET_NOT_FOUND" in result
    assert target.read_text() == (
        "def f(x):\n"
        "    # y = x + 1\n"
        "    return x + 1\n"
    )


def test_singleline_match_with_multiline_newstring_refused(workspace):
    # A single-line target matched ignoring whitespace, but a multi-line
    # new_string, must also be refused to avoid inserting a bare newline that
    # would land unindented.
    target = workspace / "code.py"
    target.write_text("    value = compute()\n")
    result = edit_file(
        str(target),
        "value=compute()",
        "value = compute()\nreturn value",
    )
    assert "EDIT_TARGET_NOT_FOUND" in result
    assert target.read_text() == "    value = compute()\n"


def test_singleline_whitespace_fallback_still_works(workspace):
    # The single-line spacing benefit from Phase Twenty must remain intact.
    target = workspace / "code.py"
    target.write_text("    return a + 0.70 * v\n")
    result = edit_file(str(target), "a + 0.70*v", "a - 0.70 * v")
    assert "ignoring whitespace" in result
    assert target.read_text() == "    return a - 0.70 * v\n"
