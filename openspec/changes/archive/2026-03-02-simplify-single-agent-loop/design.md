## Context

SuperSpec currently exposes a lease-aware pull protocol (`next`, `complete`, `fail`, `status`) to support concurrent agents, stale-claim recovery, and ownership validation. In present usage, execution is intentionally simpler: one agent, one process, serial step handling. The active protocol and guidance therefore carry complexity (lease lifecycle, invalid lease handling, lease-safe polling semantics) that does not deliver immediate value for the current operating model.

At the same time, the plan template includes advanced knobs and narrative that are useful for generalized orchestration but heavy for the near-term workflow centered on sequential OpenSpec artifact progression.

## Goals / Non-Goals

**Goals:**
- Simplify the execution contract to the minimum serial loop: `next -> execute -> complete|fail` until `done`.
- Remove lease-centric behavior from current requirements, CLI contract, and guidance.
- Simplify the default plan template to a clear single-agent serial baseline.
- Clean up obsolete code paths, tests, and docs that only support lease-based behavior.
- Keep the design reversible so lease-based concurrency can be reintroduced later in a dedicated change.

**Non-Goals:**
- Designing a new multi-agent concurrency model in this change.
- Introducing heartbeats, lease renewal, distributed coordination, or parallel DAG execution.
- Preserving backward compatibility for existing lease-dependent clients.

## Decisions

### Decision 1: Adopt single-agent serial protocol contract for current release
The protocol remains pull-based but no longer requires step leases.

- `next` returns one runnable step payload when available.
- `complete`/`fail` identify the step by `stepId` only.
- The engine assumes exclusive in-process ownership of execution state.

Rationale:
- Matches real-world execution mode today.
- Reduces cognitive and implementation load for both agent guidance and protocol clients.
- Eliminates an entire class of lease-token handling errors that are irrelevant in single-agent mode.

Alternatives considered:
- Keep lease fields but mark them optional. Rejected because it keeps dual-path complexity and weakens contract clarity.
- Keep full lease design now for future-proofing. Rejected because near-term developer ergonomics are the priority.

### Decision 2: Simplify starter plan template around sequential workflow
The default plan template should express the standard linear artifact workflow with minimal required knobs and clear single-agent assumptions.

Rationale:
- Most users start from the same sequential flow.
- Fewer optional controls in starter template lowers setup friction.
- Advanced orchestration features can be introduced by explicit customization later.

Alternatives considered:
- Preserve full generic template and rely on docs. Rejected because complexity cost appears at every initialization.

### Decision 3: Remove lease-oriented docs/tests with explicit future-reintroduction note
Documentation, skill guidance, and tests should no longer describe or assert lease lifecycle behavior in current baseline.

Rationale:
- Prevents mismatch between intended simple model and documented behavior.
- Keeps test suite aligned with intended product contract.

Alternatives considered:
- Keep lease docs as dormant references. Rejected to avoid confusion about active guarantees.

## Risks / Trade-offs

- [Risk] Dropping lease checks removes built-in protection if concurrent executors are accidentally introduced.
  - Mitigation: explicitly scope current mode to single-agent single-process in specs and docs; fail fast on unsupported concurrent usage if detectable.
- [Risk] Existing clients or scripts using `--lease` will break.
  - Mitigation: mark change as breaking in proposal/specs and update guidance/examples in one pass.
- [Risk] Future reintroduction may require another breaking transition.
  - Mitigation: keep protocol internals and docs structured so lease lifecycle can return as an additive future mode.
