"""Generation of clarifying questions for underspecified task briefs."""

from __future__ import annotations

import json
import re
from typing import Any

from agent.model import ModelClient


CLARIFY_SYSTEM_PROMPT = (
    "You assess whether a software task brief is specified well enough to "
    "begin work without risky assumptions. Consider five dimensions: the "
    "input the tool consumes; the output it produces; the scope (script, "
    "library, command-line tool, notebook, or service, and whether it is "
    "for one run or repeated use); the substantive content of the work, "
    "including any calculations, transformations, or conventions; and "
    "whether the result must match existing files or conventions. "
    "If the brief is specified well enough on the dimensions that matter "
    "for this particular task, respond that no questions are needed. "
    "Otherwise, produce up to five concise clarifying questions, covering "
    "only the dimensions the brief leaves genuinely unspecified. Do not ask "
    "about dimensions the brief already answers, and do not ask more "
    "questions than necessary. Respond strictly as JSON of the form "
    '{"needs_clarification": true, "questions": ["...", "..."]} or '
    '{"needs_clarification": false, "questions": []} with no other text.'
)

MAX_QUESTIONS = 5


def assess_brief(task: str, model: ModelClient) -> tuple[bool, list[str]]:
    """Assess a brief and return whether clarification is needed and questions.

    Returns a tuple of a boolean and a list of question strings. The boolean
    is True when the brief is underspecified and clarification is warranted.
    The list contains at most five questions. If the model's response cannot
    be parsed, the function conservatively reports that no clarification is
    needed so that the agent proceeds rather than blocking.
    """
    messages = [
        {"role": "system", "content": CLARIFY_SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    raw = model.chat(messages)
    content = raw.get("content", "") if isinstance(raw, dict) else ""

    parsed = _parse_assessment(content)
    if parsed is None:
        return False, []

    needs = bool(parsed.get("needs_clarification", False))
    questions = parsed.get("questions", [])
    if not isinstance(questions, list):
        questions = []
    questions = [str(q) for q in questions][:MAX_QUESTIONS]

    if not questions:
        return False, []
    return needs, questions


def _parse_assessment(content: str) -> dict[str, Any] | None:
    """Parse the model's JSON assessment, tolerating surrounding text."""
    if not content:
        return None
    candidate = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if match:
            candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
