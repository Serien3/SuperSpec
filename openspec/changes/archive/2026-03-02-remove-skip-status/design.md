## Context

SuperSpec currently models three action terminal outcomes (`SUCCESS`, `FAILED`, `SKIPPED`). In practice, `SKIPPED` introduces semantic overlap with failure policies and dependency gating, and makes progress accounting less intuitive. Existing protocol logic also treats `SKIPPED` as dependency-complete, which couples scheduling behavior to a non-essential status value.

## Goals / Non-Goals

**Goals:**
- Reduce action terminal semantics to two states: `SUCCESS` and `FAILED`.
- Remove `skip_dependents` policy from plan/action-level `onFail` configuration.
- Preserve deterministic orchestration by explicitly failing downstream dependents when an upstream dependency cannot succeed.
- Keep status/progress output simple and unambiguous.

**Non-Goals:**
- Redesign retry policy behavior.
- Introduce new executor types or plan schema version changes.
- Add backward-compat shims that continue emitting `SKIPPED`.

## Decisions

1. Two-terminal-state model for actions
- Decision: action terminal states are only `SUCCESS` and `FAILED`.
- Rationale: this aligns state semantics with user intent and simplifies decision logic.
- Alternative considered: keep `SKIPPED` as presentation-only alias; rejected because it keeps internal branching complexity.

2. Remove `skip_dependents` from failure policy enums
- Decision: `onFail` supports only `stop` and `continue`.
- Rationale: the difference between these policies is whether overall run halts immediately or keeps processing independent runnable actions; neither requires `SKIPPED`.
- Alternative considered: keep `skip_dependents` and map to `FAILED`; rejected because policy name becomes misleading.

3. Add explicit dependency-failure propagation
- Decision: when an action reaches non-retryable failure, all actions that (directly or transitively) depend on it are marked `FAILED` with structured dependency-failure error payload.
- Rationale: without `SKIPPED`, dependents must not remain indefinitely pending/blocked.
- Alternative considered: leave dependents pending forever and rely on terminal timeout; rejected as operationally noisy and non-deterministic.

4. Progress accounting strictness
- Decision: `progress.done` counts only `SUCCESS`; `FAILED` is separate.
- Rationale: improves observability and avoids conflating successful work with bypassed paths.

## Risks / Trade-offs

- [Risk] Existing plans may still specify `skip_dependents` and fail validation after this change.
  Mitigation: update plan schema and default templates together; provide clear validation error message.

- [Risk] Dependency-failure propagation could hide original failure context.
  Mitigation: preserve original failure in `lastFailure` semantics and encode propagated failures with explicit `dependency_failed` metadata referencing upstream action id.

- [Risk] Broad propagation in large DAGs can make many actions fail at once.
  Mitigation: deterministic event emission per propagated action for traceability.

## Migration Plan

1. Update spec requirements for protocol terminal semantics and orchestration failure-policy constraints.
2. Update schema enums and protocol engine implementation to remove `SKIPPED` paths.
3. Add/adjust tests for dependency-failure propagation and progress accounting.
4. Validate representative existing plans and fix any `skip_dependents` references.

## Open Questions

- Should propagated dependent failures be emitted as a distinct event type (e.g., `action.failed_dependency`) or reuse `action.failed` with a dedicated code?
- Should `continue` mode continue scheduling unrelated branches after root failure propagation in the same polling cycle, or only on subsequent `next` calls?
