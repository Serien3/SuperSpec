## 1. Specification and contract alignment

- [x] 1.1 Update protocol requirement text and examples to remove `SKIPPED` as an allowed action terminal state.
- [x] 1.2 Update orchestration requirements to define downstream dependency-failure propagation semantics.
- [x] 1.3 Update user-facing protocol/status contract descriptions to reflect two terminal outcomes (`SUCCESS`, `FAILED`).

## 2. Engine and schema changes

- [x] 2.1 Remove `SKIPPED` handling branches from protocol state transitions and completion accounting.
- [x] 2.2 Implement deterministic downstream failure propagation for direct and transitive dependents.
- [x] 2.3 Narrow `onFail` enum support by removing `skip_dependents` from plan schema validation.
- [x] 2.4 Ensure terminalization logic reaches a bounded terminal state without leaving dependency-blocked actions pending indefinitely.

## 3. Test coverage and compatibility checks

- [x] 3.1 Update integration tests to assert no `SKIPPED` status is emitted in any execution path.
- [x] 3.2 Add/adjust tests for dependency-failure propagation and progress field accounting (`done`, `failed`, `remaining`).
- [x] 3.3 Add validation tests that reject `onFail: skip_dependents` in plan defaults and action overrides.
- [x] 3.4 Validate representative existing plans and fixtures for compatibility with the new policy enum and status model.
