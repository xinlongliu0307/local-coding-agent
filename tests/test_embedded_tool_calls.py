# tests/test_embedded_tool_calls.py

from agent.loop import _extract_embedded_tool_calls


def test_extracts_single_json_object():
    content = '{"name": "read_file", "arguments": {"path": "a.py"}}'
    calls = _extract_embedded_tool_calls(content)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "read_file"
    assert calls[0]["function"]["arguments"] == {"path": "a.py"}


def test_extracts_object_with_single_quoted_values():
    # Python-dict style with single quotes is not valid JSON.
    # This reproduces the 32B Level Two failure.
    content = "{'name': 'edit_file', 'arguments': {'path': 'a.py', 'old_string': 'x', 'new_string': 'y'}}"
    calls = _extract_embedded_tool_calls(content)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "edit_file"
    assert calls[0]["function"]["arguments"]["old_string"] == "x"


def test_extracts_multiple_concatenated_objects():
    content = (
        "{'name': 'edit_file', 'arguments': {'path': 'a.py', 'old_string': 'a', 'new_string': 'b'}}"
        "{'name': 'edit_file', 'arguments': {'path': 'a.py', 'old_string': 'c', 'new_string': 'd'}}"
    )
    calls = _extract_embedded_tool_calls(content)
    assert len(calls) == 2
    assert [c["function"]["arguments"]["old_string"] for c in calls] == ["a", "c"]


def test_ignores_objects_without_a_known_tool_name():
    content = '{"path": "a.py", "old_string": "x"}'
    calls = _extract_embedded_tool_calls(content)
    assert calls == []
