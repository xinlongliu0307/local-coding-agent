"""Policy for what shell commands the agent may run.

This module classifies a command into one of three dispositions:

- DENIED: an irreversible or escape operation that must never run, even
  with approval. The command tool refuses it outright.
- ALLOWED: a recognised, routine command (inspection or testing) that is
  safe for ordinary work.
- UNRECOGNISED: neither denied nor explicitly allowed. The command is
  permitted to proceed to the approval gate, but is flagged so the user
  scrutinises it more carefully before approving.

The denylist is the inviolable layer and is checked first. The allowlist is
advisory and informs how loudly the approval gate should warn the user.
"""

from __future__ import annotations

import re
import shlex
from enum import Enum


class Disposition(str, Enum):
    DENIED = "denied"
    ALLOWED = "allowed"
    UNRECOGNISED = "unrecognised"


# Substrings and patterns that mark a command as irreversible or as an
# attempt to escape the working directory. Matched against the raw command
# string, because shell metacharacters are what make these dangerous.
DENY_PATTERNS: list[str] = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\brm\s+-[a-z]*r[a-z]*f\b",
    r"\bgit\s+push\b.*--force",
    r"\bgit\s+push\s+-f\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\b",
    r":\(\)\s*\{",          # fork-bomb signature
    r"\bmkfs\b",
    r"\bdd\b\s+if=",
    r">\s*/dev/sd",
    r"\bchmod\s+-R\b",
    r"\bchown\s+-R\b",
    r"\bsudo\b",
    r"\bcurl\b.*\|\s*(sh|bash)",
    r"\bwget\b.*\|\s*(sh|bash)",
    r"\beval\b",
]

# Command prefixes (first token) considered safe for routine work. A command
# whose first token is here, and which is not caught by the denylist, is
# classified ALLOWED.
ALLOW_PREFIXES: set[str] = {
    "pytest",
    "python",
    "python3",
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "rg",
    "find",
    "wc",
    "echo",
    "pwd",
    "diff",
    "git",  # git is allowed at prefix level; dangerous git is denied above
}


def classify_command(command: str) -> Disposition:
    """Classify a shell command into a Disposition.

    The denylist is checked first against the raw command string and is
    inviolable. If not denied, the first token is checked against the
    allowlist. Anything neither denied nor allowed is UNRECOGNISED.
    """
    if not command or not command.strip():
        return Disposition.UNRECOGNISED

    lowered = command.lower()
    for pattern in DENY_PATTERNS:
        if re.search(pattern, lowered):
            return Disposition.DENIED

    try:
        tokens = shlex.split(command)
    except ValueError:
        # Unparseable (e.g. unbalanced quotes): treat as unrecognised so it
        # draws scrutiny rather than being silently allowed.
        return Disposition.UNRECOGNISED

    if tokens and tokens[0] in ALLOW_PREFIXES:
        return Disposition.ALLOWED

    return Disposition.UNRECOGNISED
