# Progress

## Phase 0 — Foundations: complete (2026-07-09)

- Monorepo scaffolded: `libs/core` (schema, RLS scaffolding) + 4 service
  shells (ingestion, query, dashboard, embedding), uv workspace.
- Initial schema migration: `tenants`, `repos`, `documents`, `chunks`
  (pgvector), `pipeline_runs`, `agent_steps`, `usage_events` — every
  tenant-scoped table carries `tenant_id` from this first migration.
- RLS policies created but left inert (not yet `ENABLE`d) until Phase 3,
  per ADR 0003.
- Found and fixed a real bug while validating the RLS design: the default
  Postgres superuser role (`POSTGRES_USER` in the standard Docker image)
  bypasses RLS entirely regardless of `FORCE ROW LEVEL SECURITY`. Added a
  separate, deliberately unprivileged `asktherepo_app` role
  (migration `f36fa9caac33`) that application services connect as instead;
  migrations continue to run as the privileged role. Verified isolation
  actually works end-to-end using the restricted role, not just assumed
  from the policy SQL looking correct.
- `docker-compose up --build` verified working end-to-end: all 4 services
  start, pass health checks, and the query service was confirmed able to
  connect to Postgres as the restricted role.
- CI (GitHub Actions): lint (ruff) + type-check (mypy) + migrate + test
  against real Postgres+Redis service containers. Pushed and running at
  https://github.com/sandy181199/asktherepo/actions
- 6 ADRs written in `docs/adr/`: vector storage, orchestration, multi-tenancy
  (including the RLS/superuser pitfall), provider-agnostic LLM/embeddings,
  queue/events, license.
- Repo pushed public: https://github.com/sandy181199/asktherepo

## Next up: Phase 1 — Core engine

- GitHub repo ingestion connector (code + docs + issues/PRs)
- Language-aware chunking
- Local embedding model (pick from current benchmarks — not yet chosen,
  see ADR 0004)
- Hybrid retriever (pgvector + Postgres full-text, reciprocal rank fusion)
- Hand-rolled Planner → Retriever → Synthesizer → Critic orchestrator
- Query API + minimal HTMX dashboard
- Dogfood eval set: 30-60 hand-curated Q&A pairs about
  `Disla-Novo/Dimidium_Bellerophon`, including several grounded in the
  9 PRs already contributed to that repo
- README-as-product update once there's something real to demo

See `~/.claude/plans/reactive-jingling-bubble.md` for the full phased plan.
