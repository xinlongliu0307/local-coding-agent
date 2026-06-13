# Security Posture

This document describes the safety measures built into the agent and, as
importantly, their limits. The guiding principle is to move safety from
vigilance to structure: wherever a structural constraint can enforce a safe
outcome, it does, rather than depending on the user to catch every dangerous
case under the fatigue of a long session. No single measure is treated as
sufficient; the measures are layered, so that more than one must fail for
harm to occur.

## Threat model

The agent runs locally, executes shell commands, and reads and writes files,
under the direction of a language model that is fallible rather than
adversarial. The risks the measures address are: a destructive or
irreversible command issued in error; a file operation reaching outside the
intended working area; instructions hidden in file or command content that
the model might mistake for commands; a conversation growing until the model
degrades; and a recovery path that is assumed to work but never verified.

## Measures

### Command confinement

Shell commands run through a policy that classifies each command before
execution. A denylist of irreversible or escape operations — recursive
force-deletion, force-pushes, hard resets, privilege escalation, piping a
download into a shell, and similar — is refused outright, inside the tool,
before execution, and cannot be overridden by approval. An allowlist of
routine inspection and test commands is recognised as safe; anything neither
denied nor recognised is permitted but flagged at the approval prompt so it
draws sharper scrutiny. Every mutating command also passes the approval gate.

### File-path confinement

The file tools resolve every path against a workspace root and refuse any
path that resolves outside it, after symbolic links and parent-directory
traversal are accounted for. This confines reads and writes to a scoped
directory even when the model supplies a path — hallucinated, traversing, or
symlinked — that points elsewhere. The refusal happens inside each tool,
before any filesystem access.

### Untrusted-content marking

Output from tools that surface external content — file contents, command
output, directory listings — is wrapped in delimiters that mark it as
untrusted data, and the system prompt instructs the model to treat anything
within those delimiters as information to analyse, never as instructions to
obey. The wrapping neutralises any attempt within the content to forge the
delimiters, so injected text cannot break out of the data region. This
implements the content-segregation recommendation of OWASP LLM01:2025.

### Bounded conversation history

When a conversation grows past a threshold, the older middle is condensed
into a compact digest while the system prompt, the original task, and the
most recent exchanges are preserved, so the agent can continue on long tasks
without exhausting the model's context window.

### Verified recovery

Every file the agent changes is snapshotted before the change, with a
manifest recording each file's original location so the snapshot can be
restored to the exact paths it was taken from. Restoration is verified by a
round-trip test, files sharing a basename in different directories are each
preserved, and any file that cannot be captured is surfaced rather than
silently skipped. Restoration is an operator function, deliberately not
exposed as a model-callable tool.

## Limits

These measures raise the floor; they do not make the agent unconditionally
safe, and the project does not claim they do.

- The command denylist is not exhaustive. It makes a small set of
  catastrophic operations structurally impossible, but a sufficiently
  contrived command can express a dangerous effect the patterns do not
  match. The approval gate remains the general safeguard for what the
  denylist does not catch.
- The command tool is not yet confined to the workspace root the file tools
  enforce. A command can still read outside the working area through the
  shell. Unifying the two boundaries is a known, intended refinement.
- Content marking is a mitigation, not a guarantee. A capable injection may
  still influence a fallible model despite the markers; the approval gate
  exists to ensure a subverted model still cannot perform a destructive
  mutation without consent.
- The model is small, and its behaviour is stochastic. The structural
  measures hold regardless of the model, but the model's own judgement —
  reading before editing, recognising an injection as data — is not
  guaranteed and varies between runs.

## Reporting

This is a personal project and not intended for production use. Observations
about its security may be raised as issues on the repository.
