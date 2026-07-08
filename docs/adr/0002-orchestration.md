# ADR 0002: Multi-agent orchestration — hand-rolled state machine, not a framework

## Status

Accepted

## Context

The core query pipeline is a multi-step agent loop: a Planner classifies the
question and picks a retrieval strategy, a Retriever runs hybrid search, a
Synthesizer drafts a cited answer, and a Critic checks the draft against what
was actually retrieved, optionally looping back to the Retriever on low
confidence. Frameworks like LangGraph, CrewAI, and AutoGen exist specifically
for this kind of orchestration.

## Decision

Build the pipeline as our own typed state machine: a `PipelineState`
(Pydantic) model threaded through explicit Python nodes, with an explicit
graph of allowed transitions (including the Critic → Retriever re-retrieval
edge), rather than adopting a framework for the core loop.

## Rationale

- Owning the control flow means we can speak concretely to state persistence,
  idempotent per-step retries, timeout/cancellation semantics, structured
  output validation and repair, and confidence-gated branching — all of
  which are hidden inside a framework and hard to reason about precisely if
  we didn't build them.
- Every run's state is persisted (`pipeline_runs` / `agent_steps` tables),
  making a run resumable, replayable, and inspectable from the dashboard.
  That persistence model is ours to design because the control flow is ours.
- The amount of code this actually costs is small — an executor of a few
  hundred lines — relative to the clarity it buys.

LangGraph (or similar) was evaluated and is a reasonable choice for
*prototyping* a new agent pipeline quickly, where speed-to-first-version
matters more than owning the internals. That's not the situation here: this
pipeline is the core product, not a prototype.

## Consequences

Each agent step still calls out to an LLM through the provider-agnostic
`LLMProvider` interface (ADR 0004) — we're not reinventing prompting, only the
control flow around it. A future `/experiments` directory may hold a
separate, clearly-labeled pipeline built on a framework, specifically to
demonstrate both approaches were considered deliberately.
