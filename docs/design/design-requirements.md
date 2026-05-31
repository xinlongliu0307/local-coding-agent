# Agent Design Requirements

This document specifies the design requirements for the personal AI coding
agent to be built during Phase One onwards. It is the prescriptive
counterpart to `patterns-across-sessions.md`, which records the
observations that motivate these requirements.

This is the finalised version of the design requirements, produced during
the synthesis pass that closed Phase Zero. It consolidates the evidence
from four structured evaluation sessions of a reference coding agent into
a set of mandatory behaviours, forbidden behaviours, and operating modes
that will inform Phase One implementation. The document is stable rather
than provisional, but it remains subject to revision as implementation
reveals considerations that evaluation alone could not surface.

## 1. Purpose and Scope

The agent is a general-purpose AI coding agent that runs entirely on a
local laptop using open-weights language models served via Ollama. It
targets general software engineering tasks: multi-file edits,
refactoring, running tests, and diagnostic work. It is not specialised
for any particular research domain; atmospheric sciences is used as the
evaluation domain because it lies outside the maintainer's active
research (Southern Ocean meanders and Antarctic sea-ice altimetry) and
therefore cannot become entangled with confidential data.

The agent's design is informed by a four-session evaluation of OpenAI's
Codex CLI conducted in late May 2026. The patterns observed in those
sessions are recorded in `patterns-across-sessions.md`; this document
translates those patterns into prescriptive design constraints. The
agent is intended to replicate Codex's strengths (forward-looking error
anticipation, careful read-before-write ordering, graceful sandbox
negotiation) while addressing its weaknesses (silent assumption-making
under ambiguity, path-of-least-resistance test fixes, Git-context
assumption regardless of repository state, incomplete self-summaries).

## 2. Mandatory Behaviours

The agent must exhibit the following behaviours by design rather than by
hope. Each is mandated by an observation from Phase Zero, Week One; the
source observation is cited.

1. Read existing code in the order public-API surface, then test
   contract, then refactor target, then build configuration, then
   entry point, when starting any task that modifies existing code.
   (Source: Variation 2's clean refactor.)

2. Pre-emptively declare expected dependencies, tools, and PATH
   locations before they are needed. (Source: Saturday's proactive
   pytest declaration.)

3. Use Python's `is` operator to test object identity, not just value
   equality, when verifying that a refactor has moved code between
   modules rather than duplicating it. (Source: Variation 2's
   boundary tests.)

4. Declare its mode (ask, prototype, or commit) explicitly at the
   start of each task, and justify the choice in one sentence.
   (Source: Variation 1's fresh-instance reflection.)

5. Detect Git repository presence explicitly at session start and
   surface the result in the opening environment summary, rather than
   issuing `git status` or `git log` reflexively. (Source: the Git-
   context assumption observed in all three sessions.)

6. When working in a scientific computing domain (identified by the
   presence of numpy, pandas, xarray, MetPy, or similar imports),
   require explicit declaration of units and data sources in the
   agent's preamble before any calculation is performed. (Source:
   Variation 1's fresh-instance reflection on domain-contract
   underspecification.)

7. Select reading order by task type. For refactor and modification
   tasks, read in the order public-API surface, then test contract,
   then implementation, then build configuration, then entry point.
   For diagnostic tasks, read in execution-pipeline order: entry
   point, then suspected calculation module, then data loading,
   then tests, then configuration. Declare the chosen order
   explicitly in the preamble. (Source: Variation 2's refactor
   reading order; Variation 3's diagnostic reading order.)

8. Articulate a confidence level for each proposed change in
   diagnostic work, stated before the verification step rather than
   after it. The confidence statement should be brief (one or two
   sentences) and should give the user a basis for trusting or
   questioning the fix before tests are run. (Source: Variation 3's
   wrap-up summary.)

9. Produce a file-content snapshot of all modified files at the end of
   every task, stored under a hidden agent directory with a thirty-day
   pruning policy, so that verification by external review does not
   depend on diffs alone. (Source: the diff-based reading error during
   the refactor evaluation review.)

10. Reproduce a user-reported symptom before reading code on any
    diagnostic task where the agent has not already run the affected
    code in the current session. Where the agent has already run the
    code and observed the symptom, reproduction is optional. (Source:
    the diagnostic evaluation session's trust of an unverified symptom.)

11. Default to step-by-step approval for diagnostic and destructive
    tasks, and to batched approval for scaffolding and refactor tasks.
    The approval cadence is declared in the agent's opening message
    alongside the mode declaration. (Source: the diagnostic evaluation
    session's per-command approval, which produced a legible narrative
    and suppressed the reflexive version-control assumption.)

## 3. Forbidden Behaviours

The agent's system prompt and harness must structurally prevent the
following behaviours. Each is forbidden because Codex exhibited it and
the consequence was visible degradation of either output quality or
user experience.

1. Deleting failing assertions to clear test failures. The agent must
   propose a code fix or articulate why the assertion is incorrect;
   it must not modify the assertion to make the test pass without
   addressing what the assertion was checking. (Source: Saturday's
   and Variation 1's path-of-least-resistance test fixes.)

2. Presenting action statements as if they were assumption statements.
   The agent must distinguish between "I will do X" (an action) and
   "I am assuming Y about your intent" (a redirectable interpretation),
   and must use the latter form before any code is written under
   ambiguity. (Source: Variation 1's preamble behaviour.)

3. Producing self-summaries that omit unexpected good work or
   unexpected shortcuts taken. The wrap-up protocol must require
   explicit enumeration of both categories, framed separately rather
   than folded into a general narrative. (Source: Saturday's omission
   of the pandas refactor; Variation 1's omission of the test-fix
   shortcut.)

4. Relying on diff-based verification alone. The harness must produce
   file-content verification artefacts in addition to diffs, because
   diffs hide what is preserved and can be misread. (Source: the
   diff-based reading error during Variation 2 review.)

5. Treating workspace context as inert. Unexpected files, unexpected
   comments, or unexpected metadata must be surfaced as questions for
   the user rather than acted on without comment. (Source: Variation 1
   reading observations.md without engaging with its content.)

6. Assuming Git context. Filesystem operations and Git operations must
   be selected based on detected repository state, not on a default
   that assumes Git is present. (Source: all three sessions.)

7. Bundling adjacent improvements into the same patch as the
   requested work. Proactive quality improvements that the brief did
   not request must be proposed as separate patches, each with its
   own approval moment. The agent may identify and propose such
   improvements, but it must not bundle them into the main patch
   without explicit user permission. (Source: Variation 3's
   test-bound tightening bundled with the bug fix.)

## 4. The Three-Mode Disposition

The agent operates in one of three modes at any given time, selected
explicitly at the start of each task and re-evaluated when significant
new information arrives.

**Ask mode.** Used when the brief is underspecified at the domain-
contract level — when the wrong assumption would produce a structurally
different tool rather than a stylistically different one. In ask mode,
the agent issues five-or-fewer clarifying questions covering input
format, output format, scope, scientific content, and convention-
matching, and waits for the user's responses before writing code.

**Prototype mode.** Used when the brief is underspecified at the UI
level — when reasonable defaults can be set, the user can adjust them
afterwards, and the stakes of a wrong default are bounded. In prototype
mode, the agent proceeds with defaults but labels the output as
exploratory and revisable, and explicitly invites the user to redirect
before further work is built on top of it.

**Commit mode.** Used when the brief is sufficiently specified that
"good" has a defined meaning and the agent can iterate against that
standard. In commit mode, the agent proceeds without clarification but
must still satisfy all mandatory behaviours from Section Two.

The mode is declared in the agent's opening message of each task, and
is re-declared whenever the mode changes during a session.

## 5. The Clarifying-Question Protocol

When the agent is in ask mode, the clarifying-question protocol applies.
The protocol is bounded at five questions to prevent interrogation
fatigue and is structured around five dimensions, each of which must be
addressed if it is not already specified in the brief.

1. **Input.** What data is the tool expected to consume? File format,
   source, schema, and any conventions the tool must respect.

2. **Output.** What artefact is the tool expected to produce? Format,
   destination, structure, and consumer.

3. **Scope.** Is this a single-purpose script, a reusable library, a
   command-line tool, an interactive notebook, or a service? Is it
   intended for one run or for repeated use?

4. **Scientific content.** Which calculations, transformations, or
   diagnostics are required? Which are optional? Are there
   established libraries or conventions that should be preferred?

5. **Convention-matching.** Are there existing sample files, prior
   tools, or institutional conventions that the new tool must
   resemble or interoperate with?

The agent must not ask all five questions if some are already answered
in the brief; the protocol is structured around dimensions, not
questions per se, and absent dimensions are the only ones to be
queried. If fewer than three dimensions are unspecified, the agent
prefers prototype mode over ask mode to keep momentum.

## 6. Verification and Self-Reporting

At the end of each task, the agent must produce a self-summary that
explicitly enumerates the following categories. Each category is a
separate section of the summary; categories must not be merged.

1. **Files created, modified, and preserved.** Listed by path and by
   type of change. File content, not diff content, is the
   authoritative form.

2. **Tests run, with results.** Every test execution during the
   session is listed, with the outcome and any noteworthy timing
   information.

3. **Deviations from the brief, if any.** The agent must explicitly
   state where its work deviates from the original brief and why,
   including any scope reductions, scope additions, or unilateral
   decisions made under ambiguity.

4. **Unexpected good work, if any.** Quality-aware iteration that
   exceeded the brief must be reported explicitly, not folded into
   the general narrative.

5. **Unexpected shortcuts taken, if any.** Path-of-least-resistance
   fixes, deferred concerns, or known incomplete work must be
   reported explicitly. The agent must not present a shortcut as a
   completed task without flagging the shortcut.

The harness produces a file-content snapshot of all modified files at
the end of each session, preserved alongside the session log, so that
verification by external review does not depend on diffs alone.

## 7. Resolved Design Decisions

The questions that were open during the evaluation phase have been
resolved during the synthesis pass. Each resolution is recorded here for
provenance; the resolutions that constitute new behavioural rules have
been incorporated into Sections Two and Three.

**Whether diagnostic work warrants a fourth mode.** Resolved: no. The
existing commit mode, combined with the task-type-dependent reading-order
requirement and the confidence-articulation requirement, covers the
observed diagnostic behaviour. Introducing a fourth mode would add
conceptual overhead without capturing any behaviour that the existing
modes plus the diagnostic-specific requirements do not already address.

**Whether the boundary-test design pattern generalises across task
types.** Resolved: partially, as a task-type-dependent principle. The
governing rule is that the agent should produce tests that exclude the
most recent failure mode. For refactors, this means identity checks that
confirm code was moved rather than duplicated; for diagnostic fixes, it
means tight regression bounds around the known-correct value. The pattern
is therefore encoded by task type rather than as a single universal rule.

**Whether the clarifying-question protocol is triggered by mode
declaration or by an automated heuristic.** Resolved: by explicit mode
declaration. The three-mode disposition already requires the agent to
declare its mode at the start of each task, and the clarifying-question
protocol attaches naturally to ask mode. No separate heuristic is needed.

**Whether file-content verification snapshots are automatic or
on-request.** Resolved: automatic. The agent produces a file-content
snapshot of all modified files at the end of every task, stored under a
hidden agent directory, with a thirty-day pruning policy appropriate to
personal-scale use. This decision is incorporated as a mandatory
behaviour in Section Two.

**Whether the mode declaration is visible in real time or logged for
later review.** Resolved: visible in real time. The diagnostic evaluation
session demonstrated that a visible reasoning narrative produces a more
legible process; the same principle applies to mode declarations, which
are surfaced in the agent's opening message for each task.

**Whether user-reported symptoms must be reproduced before code is
read.** Resolved: mandatory for diagnostic tasks where the agent has not
already run the code in the current session, and optional where it has.
The diagnostic evaluation session showed the agent trusting a reported
symptom without independent reproduction, which produced a correct fix in
that instance but would risk a fast wrong fix where the report is
inaccurate. This decision is incorporated as a mandatory behaviour in
Section Two.

**Whether step-by-step approval is the default cadence.** Resolved:
step-by-step approval is the default for diagnostic and destructive
tasks, and the lower-overhead batched-approval cadence is the default for
scaffolding and refactor tasks. The diagnostic evaluation session
demonstrated that per-command approval both produced a legible narrative
and suppressed the reflexive version-control assumption. This decision is
incorporated as a mandatory behaviour in Section Two.

All resolutions above remain subject to revision as Phase One
implementation reveals considerations that evaluation alone could not
surface.

## 8. Provenance

These requirements are grounded in four structured evaluation sessions of
a reference coding agent conducted in late May 2026. The sessions examined
scaffolding under a well-specified brief, behaviour under a deliberately
ambiguous brief, multi-file refactoring under constraint, and diagnostic
bug-hunting. Each session was documented in an observation record, and the
behavioural patterns observed across sessions were consolidated into a
companion patterns document before being translated into the prescriptive
constraints recorded here. The underlying observation records are preserved
in the maintainer's personal archive and are not part of this repository.