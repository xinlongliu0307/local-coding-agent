"""A mutating tool that executes a shell command under approval."""

from __future__ import annotations
from agent.command_policy import classify_command, Disposition

import subprocess


TIMEOUT_SECONDS = 120
MAX_OUTPUT_CHARS = 8000


def run_command(command: str) -> str:
    """Run a shell command and return its combined output and exit code.

    This tool can do anything a shell can do and is therefore classified as
    mutating: every invocation requires approval, and the approval prompt
    shows the exact command. The command is run with a timeout, and output
    is truncated to a bounded length so a verbose command cannot flood the
    conversation.
    """
    if not command.strip():
        return "Error: an empty command is not allowed."
    
    disposition = classify_command(command)
    if disposition is Disposition.DENIED:
        return (
            "COMMAND_REFUSED: this command is blocked by policy because it is "
            "irreversible or escapes the working directory, and will not be "
            "run even with approval. If you need this effect, ask the user to "
            "perform it manually."
        )

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return (
            f"Error: the command did not finish within "
            f"{TIMEOUT_SECONDS} seconds and was stopped."
        )

    parts = [f"exit code: {completed.returncode}"]
    if completed.stdout:
        parts.append("stdout:\n" + completed.stdout)
    if completed.stderr:
        parts.append("stderr:\n" + completed.stderr)
    output = "\n".join(parts)

    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n(output truncated)"
    return output
