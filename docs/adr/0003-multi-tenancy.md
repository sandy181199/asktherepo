# ADR 0003: Multi-tenancy — row-level isolation via Postgres RLS

## Status

Accepted

## Context

The product is intended to become a public multi-tenant SaaS. The usual
options for tenant isolation in a relational database are: a separate
database per tenant, a separate schema per tenant, or a shared schema with a
`tenant_id` column on every table.

## Decision

Shared database, shared schema, `tenant_id` on every table (including the
embeddings table), with isolation enforced by Postgres Row-Level Security
policies rather than trusted-by-convention application code.

## Rationale

- Database-per-tenant means migrations run N times and cross-tenant
  admin/analytics queries become federated queries — the right shape for
  enterprise single-tenant deployments, not an early SaaS with many small
  tenants.
- Schema-per-tenant is a middle ground with the same migration multiplication
  problem, and it doesn't map cleanly onto `pgvector`: it would mean one HNSW
  index per schema instead of one shared, resource-pooled index.
- Row-level with RLS is the standard, well-proven pattern for Postgres-backed
  multi-tenant SaaS at this scale. Crucially, RLS means a future bug in
  application code (a forgotten `WHERE tenant_id = ...`) still cannot leak
  data across tenants, because the database itself refuses the read — the
  isolation is structural, not just a code-review convention.

## Consequences

`tenant_id UUID NOT NULL` is added to every table starting with the very
first migration, even though Phase 1 hardcodes a single `DEFAULT_TENANT_ID`
for the single-player open-source demo experience. Retrofitting a
`tenant_id` column onto live tables with real data later is exactly the
painful migration this avoids — adding it now costs nothing.

The authentication middleware resolves the caller's tenant and sets the
Postgres session variable RLS depends on at the start of every
request/transaction; no handler threads `tenant_id` through business logic
by convention alone.

Turning multi-tenancy "on" later (enabling auth, activating RLS policies,
removing the `DEFAULT_TENANT_ID` shortcut) is therefore a comparatively small
phase, not a schema redesign.

## A pitfall found while validating this decision

RLS policies were created in the initial migration but deliberately left
inert (not yet `ENABLE`d) until Phase 3 — see the migration for
`tenant_isolation` policies. Testing that inert state manually surfaced a
real gotcha worth recording: Postgres superusers, and any role granted
`BYPASSRLS`, ignore RLS policies entirely, *even with `FORCE ROW LEVEL
SECURITY` set*. The default database role created by the standard Postgres
Docker image (`POSTGRES_USER`) is a superuser with `BYPASSRLS` — exactly the
role migrations run as. Had application services also connected with that
role, every RLS policy in this system would have silently done nothing.

Fix: a dedicated `asktherepo_app` role (migration
`f36fa9caac33_restricted_app_role_for_rls_enforcement`) with explicit
`NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE` and only the table grants
it needs (`SELECT, INSERT, UPDATE, DELETE`, no DDL). Migrations continue to
run as the privileged role; every application service connects as
`asktherepo_app`. Verified directly: with RLS temporarily enabled on `repos`
for testing, the superuser role saw all rows regardless of
`app.tenant_id`, while `asktherepo_app` correctly saw only the matching
tenant's rows, and saw none at all with no tenant context set.
