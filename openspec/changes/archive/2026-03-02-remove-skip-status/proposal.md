## Why

The execution model currently exposes three step terminal states (`SUCCESS`, `FAILED`, `SKIPPED`), which makes dependency and progress semantics harder to reason about. We want a cleaner model where every step ends as either success or failure, reducing ambiguity in orchestration and status reporting.

## What Changes

- Remove `SKIPPED` as an step terminal state from protocol semantics.
- Remove `skip_dependents` from failure policy options; keep only `stop` and `continue`.
- Introduce deterministic downstream failure propagation for dependency graphs (dependents of failed steps become failed with explicit dependency-failure reason).
- Update progress/status aggregation to count only `SUCCESS` as done and `FAILED` as failed.
- Update plan schema enums and protocol contracts to match the two-terminal-state model.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-driven-plan-execution`: step lifecycle, fail semantics, terminalization, and status aggregation change to remove `SKIPPED` and support dependency-failure propagation.
- `change-plan-orchestration`: allowed failure policy values for plan/steps are narrowed by removing `skip_dependents`.

## Impact

- Affected code: `superspec/engine/protocol.py`, `superspec/schemas/plan.schema.json`, protocol/status contract payloads, and related integration tests.
- Behavior change: plans that previously relied on `skip_dependents` or `SKIPPED` status must use new two-terminal-state semantics.
- CLI/API consumers of status output will observe no `SKIPPED` values after migration.
