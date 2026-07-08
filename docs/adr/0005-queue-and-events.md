# ADR 0005: Queue and event backbone — Redis Streams, not Kafka, for now

## Status

Accepted

## Context

The ingestion pipeline needs async task processing (chunk → embed → upsert)
and, eventually, event fan-out to multiple consumers (usage metering,
notifications, analytics). Kafka is the obvious "production event streaming"
answer, but it's also a second stateful distributed system to operate.

## Decision

Use Redis Streams (with Celery on top of Redis for task semantics — retries,
scheduling, backoff) for both task queuing and event fan-out through at least
the multi-tenancy phase. Do not introduce Kafka until there's a concrete need
for it.

## Rationale

- Redis is already required for caching and rate-limiting, so Streams is
  infrastructure we already run, not a new system.
- Consumer groups give at-least-once delivery, per-consumer offsets, and
  pending-entry lists for retry/dead-lettering — enough durability for the
  ingestion pipeline and agent-step events at this stage.
- Kafka earns its complexity when there are genuinely multiple independent
  consumer services needing durable replay-from-offset, or throughput a
  single Redis instance can't handle. Standing up Kafka for a single-consumer
  MVP is choosing infrastructure for its name recognition, not its fit.

## Consequences

Event schemas are versioned (a CloudEvents-style envelope: type, source,
time, tenant_id, payload) from the start, so that migrating the *transport*
to Kafka later — if a concrete trigger is hit — is a swap of the
producer/consumer adapter behind an interface, not a redesign of the event
model itself.
