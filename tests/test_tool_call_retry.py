from agent.loop import _looks_like_attempted_tool_call


def test_detects_unparseable_tool_call():
    content = '{"name": "write_file", "arguments": {"path": "a.py", "content": "x"""y"}}'
    assert _looks_like_attempted_tool_call(content) is True


def test_detects_concatenated_attempts():
    content = '{"name": "edit_file", "arguments": {}}{"name": "edit_file", "arguments": {}}'
    assert _looks_like_attempted_tool_call(content) is True


def test_plain_prose_is_not_a_tool_call():
    assert _looks_like_attempted_tool_call(
        "The bug is a sign error in the wind term; I have fixed it.") is False


def test_prose_mentioning_a_tool_is_not_a_tool_call():
    assert _looks_like_attempted_tool_call(
        "You could use write_file to create that module yourself.") is False


def test_empty_content_is_not_a_tool_call():
    assert _looks_like_attempted_tool_call("") is False
