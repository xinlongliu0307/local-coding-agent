"""Registry mapping tool names to their implementations, schemas, and safety."""

from __future__ import annotations

from typing import Any, Callable

from agent.tools.list_files import list_files
from agent.tools.read_file import read_file
from agent.tools.write_file import write_file
from agent.tools.edit_file import edit_file
from agent.tools.search_files import search_files
from agent.tools.run_command import run_command


# The callable implementation for each tool, keyed by tool name.
TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "search_files": search_files,
    "run_command": run_command,
}


# Tools whose output is external content the agent did not author, and which
# must therefore be marked as untrusted data before entering the model's
# context. This is orthogonal to MUTATING_TOOLS: run_command is mutating yet
# content-returning, while write_file is mutating but returns only a status.
CONTENT_RETURNING_TOOLS: set[str] = {
    "list_files",
    "read_file",
    "search_files",
    "run_command",
}


# The set of tools that mutate state and therefore require approval before
# execution. Tools not in this set are read-only and run without approval.
MUTATING_TOOLS: set[str] = {
    "write_file",
    "edit_file",
    "run_command",
}


# The schema definitions advertised to the model, following the format the
# Ollama tool-calling API expects.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List the files and directories in a given directory. "
                "Returns a newline-separated listing. Read-only and safe."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": (
                            "The directory to list. Defaults to the current "
                            "directory if not specified."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read and return the full contents of a file. Read-only "
                "and safe."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to read.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file, creating it or overwriting it. "
                "This changes the filesystem and requires user approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Replace an exact, unique occurrence of existing text in a "
                "file with new text. The old text must appear exactly once; "
                "if it is absent or ambiguous, no change is made. This "
                "changes the filesystem and requires user approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to edit.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": (
                            "The exact existing text to replace, including "
                            "surrounding context to make it unique."
                        ),
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The text to substitute in its place.",
                    },
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": (
                "Search file contents under a directory for a literal "
                "substring. Returns 'path:line: text' matches, capped at 50. "
                "Read-only and safe."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The literal text to search for.",
                    },
                    "directory": {
                        "type": "string",
                        "description": (
                            "The directory to search under. Defaults to the "
                            "current directory."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command and return its exit code and output. "
                "Use this to run tests or inspect the environment. Every "
                "invocation requires user approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                },
                "required": ["command"],
            },
        },
    },
]