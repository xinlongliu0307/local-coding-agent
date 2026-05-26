# local-coding-agent

A local, open-weights AI coding agent for general software engineering,
designed to run entirely on a personal laptop using language models
served via Ollama. The agent targets multi-file edits, refactoring, and
diagnostic work, with atmospheric sciences serving as the evaluation
domain during development.

## Status

In design phase. No implementation exists yet. This repository
currently contains the design requirements document that specifies the
agent's intended behaviour. Implementation begins in Phase One.

## Design

The agent's design is grounded in four structured evaluation sessions
of OpenAI's Codex CLI conducted in late May 2026. The sessions covered
scaffolding work under a well-specified brief, behaviour under a
deliberately ambiguous brief, multi-file refactoring under constraint,
and diagnostic bug-hunting. The patterns observed in those sessions
are translated into mandatory and forbidden behaviours in
`docs/design/design-requirements.md`.

The design requirements document specifies the agent's intended
behaviour across eight sections, covering purpose and scope, mandatory
behaviours, forbidden behaviours, the three-mode disposition (ask,
prototype, commit), the clarifying-question protocol, verification
and self-reporting requirements, and the open questions that remain
for later resolution.

## Roadmap

The project follows an eight-phase build plan. Phase Zero, covering
design and reference-agent evaluation, is complete with this commit.
Phase One will begin implementation in Python using a minimal ReAct
loop against a local Ollama server. Subsequent phases will add file
manipulation tools, persistent context, sandboxing and approval
policies, multi-file indexing, MCP client support, a textual TUI,
and an evaluation harness. The detailed roadmap will be added to
this README as phases are completed.

## Contributing

Contributions are not yet accepted. The project is at the design stage
and the maintainer is still working out the architecture. The
repository will become contribution-ready when Phase One is complete.

## License

Apache 2.0. See `LICENSE` for details.