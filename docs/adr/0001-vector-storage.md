# ADR 0001: Vector storage — pgvector in Postgres, not a dedicated vector DB

## Status

Accepted

## Context

The retrieval layer needs to store and search embeddings for chunks of ingested
content (code, docs, issues/PRs). The obvious options are a dedicated vector
database (Qdrant, Weaviate, Milvus, Pinecone) or an extension on top of the
relational database we already need (Postgres + `pgvector`).

We also need a relational store regardless, for tenants, users, API keys,
ingestion job state, and document/chunk metadata.

## Decision

Use Postgres with the `pgvector` extension for embeddings, in the same
database as everything else, through at least the multi-tenancy phase of the
roadmap.

## Rationale

- One database means tenant-data deletion is a single transaction across
  relational rows and vectors. A separate vector store means eventual
  consistency and orphaned-vector cleanup jobs — a real bug class we'd rather
  not own this early.
- Row-level tenant isolation (see ADR 0003) applies uniformly to the vector
  table the same way it applies to every other table, instead of needing a
  second, different isolation model in a second system.
- `pgvector` with HNSW indexing comfortably handles low tens of millions of
  vectors with good recall/latency — far beyond an early product's actual
  scale.
- Running a second stateful system before there's a concrete reason is
  operational overhead with no payoff yet.

## Consequences

The retrieval layer is built behind a `VectorStore` interface (in
`asktherepo_core`), so swapping to a dedicated vector database later is a
plug-in, not a rewrite. The trigger for reconsidering this decision is
explicit, not a vague "if it gets big": more than roughly 20 million chunks,
or a documented p95 vector-search latency budget violated even after tuning
HNSW's `ef_search` and index maintenance, or a need for a feature `pgvector`
doesn't do well (sharding, server-side reranking, multi-vector search).
