## Context

SuperSpec aims to extend spec-driven development by introducing a change-level execution plan (`plan.json`) that orchestrates artifact creation and implementation actions in a predictable sequence. The current repository has OpenSpec workflow support but no orchestration layer for multi-step execution, retries, or resume semantics.

The target of this change is an initial prototype that keeps compatibility with OpenSpec-style artifacts while introducing a minimal plan engine contract.

## Goals / Non-Goals

**Goals:**
- Define a stable `plan.json` schema (`superspec.plan/v1.0.0`) scoped to a single change.
- Define an action model with dependency ordering and unified execution contract.
- Support five OpenSpec-style actions: `proposal`, `specs`, `design`, `tasks`, and `apply`.
- Define run-state persistence and per-action logs for resumable execution.

**Non-Goals:**
- Implement parallel DAG scheduling.
- Implement cross-change orchestration.
- Replace OpenSpec artifact semantics or schema behavior.
- Build a full policy/rules engine beyond minimal validation.

## Decisions

### Decision 1: Change-scoped plan as source of truth
Use `openspec/changes/<change>/plan.json` as the only execution contract for that change.

Rationale:
- Keeps plan ownership close to artifacts.
- Makes plan review part of change review.
- Avoids global orchestration state that is harder to reason about.

Alternatives considered:
- Centralized global plans directory. Rejected due to weak locality and harder traceability.

### Decision 2: Two execution backends behind one action contract
Actions may run via `skill` or `script` executors, but both must return a normalized result payload.

Rationale:
- Enables incremental delivery: start with skills, add scripts selectively.
- Keeps orchestrator simple and extensible.

Alternatives considered:
- Skill-only execution. Rejected because scripted deterministic steps are often better for setup/checks.

### Decision 3: Sequential execution with explicit dependencies for v1.0.0
Actions execute in deterministic order honoring `dependsOn`; no parallel execution in first increment.

Rationale:
- Reduces engine complexity and race conditions.
- Sufficient for first adoption and debugging.

Alternatives considered:
- Full DAG executor in v1.0.0. Rejected as premature complexity.

### Decision 4: Persist run state in change directory
Persist latest state at `run-state.json` and detailed run artifacts under `runs/<run-id>/`.

Rationale:
- Enables `--resume` after interruption.
- Makes execution auditable and debuggable per action.

Alternatives considered:
- In-memory only state. Rejected due to fragility and poor operability.

## Risks / Trade-offs

- [Risk] Action type definitions drift from actual implementation. → Mitigation: lock `v1.0.0` action I/O contracts and validate at runtime.
- [Risk] Skill outputs are inconsistent and hard to parse. → Mitigation: require structured output envelope for every skill action.
- [Risk] Users overfit plan schema too early. → Mitigation: keep schema minimal and versioned; defer advanced features to later versions.
- [Risk] `apply` action scope becomes ambiguous (implementation vs verification). → Mitigation: document v1.0.0 boundary and add explicit follow-up action types in future versions.
