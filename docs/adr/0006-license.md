# ADR 0006: License — Apache-2.0 for the core engine

## Status

Accepted

## Context

This project is open source but is also intended to become a SaaS product.
Fully permissive licenses (MIT, Apache-2.0) maximize adoption but offer no
protection against a well-funded competitor hosting a clone of the service.
Source-available licenses (e.g. BSL) protect the commercial layer at the cost
of contributor friction and ongoing license-management overhead.

## Decision

License the core engine (everything in this repository: ingestion,
retrieval, orchestration, dashboard) under Apache-2.0. Any future
SaaS-specific code that doesn't belong in an open engine — billing
integration, multi-tenant provisioning specific to the hosted product —
lives in a separate, private repository that depends on this one as a
library, rather than being open-sourced under a restrictive license.

## Rationale

- Apache-2.0 over MIT specifically for its explicit patent grant, relevant
  given the project integrates multiple third-party LLM/embedding providers.
- Maximizing genuine adoptability, forkability, and star-worthiness is the
  more valuable outcome for this project's engine right now than protecting
  a commercial layer that doesn't exist yet.
- Keeping SaaS-specific orchestration code in a separate private repository
  sidesteps the licensing tradeoff entirely rather than requiring a dual- or
  source-available license on this codebase.

## Consequences

If a real, competitively-exposed hosted product exists later and this
decision needs revisiting (e.g. a source-available license for the private
SaaS layer specifically), that is a decision for that point in time, made
with an actual product and actual competitive risk in view — not a decision
to make speculatively now.
