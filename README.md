# AskTheRepo

Ask natural-language questions about a codebase and get cited, verified
answers — not a chatbot wrapped around a vector search, but a small
multi-agent pipeline that plans a retrieval strategy, retrieves, drafts an
answer with citations, and checks its own work before returning it.

**Status: early — Phase 0 (foundations) complete, Phase 1 (the core engine) in progress.**
See the [roadmap](#roadmap) below for what that means concretely.

## Why this exists

Most "chat with your repo" tools are a thin RAG wrapper: embed some chunks,
stuff the closest ones into a prompt, hope for the best. This project takes
a more deliberate approach on both ends:

- **Multi-agent, not single-shot.** A Planner decides whether a question
  needs code search, doc search, or both. A Retriever runs hybrid
  (vector + keyword) search. A Synthesizer drafts an answer with citations.
  A Critic checks those citations against what was actually retrieved, and
  can trigger another retrieval pass if it isn't confident — before you ever
  see the answer.
- **The orchestration is hand-built**, not a thin wrapper around an agent
  framework, specifically so it can support things frameworks often hide:
  resumable/replayable pipeline runs, per-step retries, and a
  confidence-gated retry loop. See [ADR 0002](docs/adr/0002-orchestration.md).
- **Multi-tenancy is designed in from the first migration** (every table
  carries a `tenant_id`, isolation is enforced with Postgres Row-Level
  Security), even though the current single-player mode doesn't need it yet.
  See [ADR 0003](docs/adr/0003-multi-tenancy.md).

## Architecture

```
                    ┌─────────────┐
                    │  Dashboard  │  FastAPI + Jinja2/HTMX
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐        ┌───────────┐
                    │    Query    │───────▶│ Embedding │  local sentence-
                    │  (agents)   │        │  service  │  transformers model
                    └──────┬──────┘        └───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐           ┌──────▼──────┐
       │  Postgres   │           │    Redis    │
       │  + pgvector │           │  (queue +   │
       │             │           │   cache)    │
       └──────▲──────┘           └──────▲──────┘
              │                         │
       ┌──────┴──────┐                  │
       │  Ingestion  │──────────────────┘
       │  (GitHub →  │
       │   chunks →  │
       │  embeddings)│
       └─────────────┘
```

Each service is a thin FastAPI app depending on the shared `asktherepo-core`
library (schema models, provider interfaces, the orchestrator) — see the
[repo layout](#repo-layout) below. Key architectural decisions are written up
as ADRs in [`docs/adr/`](docs/adr/); read those before the code if you want
the "why," not just the "what."

## Quickstart

Requires Docker (or a Docker-compatible runtime like [colima](https://github.com/abiosoft/colima)).

```bash
git clone https://github.com/sandy181199/asktherepo.git
cd asktherepo
docker compose up --build
```

This brings up Postgres (with `pgvector`), Redis, runs migrations, and starts
all four services:

| Service    | Port | Health check                       |
|------------|------|-------------------------------------|
| dashboard  | 8000 | `curl localhost:8000/health`         |
| embedding  | 8001 | `curl localhost:8001/health`         |
| ingestion  | 8002 | `curl localhost:8002/health`         |
| query      | 8003 | `curl localhost:8003/health`         |

Phase 1 (in progress) will make this actually useful: point it at a GitHub
repo and ask it questions through the dashboard. Right now these are health
endpoints only — the ingestion/retrieval/agent pipeline is being built next.

## Local development

```bash
uv sync --all-packages   # installs every workspace package into one venv
uv run pytest            # run all tests
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy libs services
```

Migrations (Alembic):

```bash
export DATABASE_URL="postgresql+psycopg://asktherepo:asktherepo@localhost:5432/asktherepo"
uv run --package asktherepo-core alembic upgrade head
```

## Roadmap

- [x] **Phase 0 — Foundations.** Workspace scaffold, schema + migrations
      (with `tenant_id` and RLS designed in from day one), `docker-compose up`,
      CI, ADRs for the core architecture decisions.
- [ ] **Phase 1 — Core engine.** GitHub ingestion, hybrid retrieval, the
      Planner/Retriever/Synthesizer/Critic pipeline, a dashboard to ask
      questions and see cited answers and pipeline traces, a hand-curated
      evaluation set. This is the milestone that makes the project actually
      usable end to end.
- [ ] **Phase 2 — Production hardening.** Tracing/metrics per agent step,
      an automated eval gate in CI, rate limiting, the first real cloud
      deploy.
- [ ] **Phase 3 — Multi-tenancy.** Auth, per-tenant API keys, RLS switched
      from designed-in to enforced, Kubernetes manifests.
- [ ] **Phase 4 — Billing & public launch.** Usage-based billing, quotas,
      legal review of ToS/Privacy Policy before any real customer's private
      code is processed.

## Repo layout

```
libs/core/          shared schema models, provider interfaces, orchestrator
services/ingestion/  GitHub connector, chunking, embedding upsert
services/query/       the agent pipeline
services/dashboard/   FastAPI + Jinja2/HTMX web UI
services/embedding/   local embedding model server
migrations/          Alembic migrations
docs/adr/            architecture decision records
infra/               Docker, Kubernetes, Terraform
eval/                golden Q&A set + evaluation harness (Phase 1+)
```

## License

Apache-2.0 — see [LICENSE](LICENSE) and [ADR 0006](docs/adr/0006-license.md)
for the reasoning.
