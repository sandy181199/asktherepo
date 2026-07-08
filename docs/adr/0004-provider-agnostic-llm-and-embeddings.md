# ADR 0004: Provider-agnostic embedding and LLM interfaces

## Status

Accepted

## Context

The pipeline needs an embedding model (for ingestion and retrieval) and an
LLM (for the Planner/Synthesizer/Critic reasoning steps). Hard-coding a
single provider for either is a lock-in and cost risk, and makes the
"no vendor lock-in" claim untestable.

## Decision

Define small `EmbeddingProvider` and `LLMProvider` interfaces in
`asktherepo_core`. Default embeddings to a local, self-hosted
`sentence-transformers` model (chosen at implementation time from current
retrieval benchmarks, not locked in ahead of time) served by the embedding
service. Default LLM reasoning to a hosted provider (Anthropic Claude), with
a documented, working fallback to a locally-hosted open-weight model for the
same interface.

## Rationale

- Embeddings are the highest-volume call in the system — every chunk of
  every ingested repo. Self-hosting them removes a hard external dependency
  from the most call-heavy part of the pipeline and keeps ingestion
  cost-free per token.
- LLM reasoning calls are lower-volume and benefit most from frontier-model
  quality on multi-step reasoning and citation-checking, which is why that
  side defaults to a hosted API rather than self-hosting from day one.
- Logging provider, model, and token counts on every call from the start
  means cost and quality can be compared empirically across providers later,
  rather than asserted.

## Consequences

Provider selection is config-driven (environment variable or, later,
tenant-level setting), not hard-coded into call sites. Swapping providers is
a configuration change.
