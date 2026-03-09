## 1. Bootstrap SuperSpec plan foundation

- [x] 1.1 Create initial `superspec/` project structure (`engine`, `runners`, `steps`, `schemas`, `templates`).
- [x] 1.2 Add `plan.schema.json` for `superspec.plan/v1.0.0` with top-level and step-level validation.
- [x] 1.3 Add `plan.template.json` for change-scoped default plan initialization.

## 2. Build core plan orchestration flow

- [x] 2.1 Implement plan loader and validator (`schemaVersion`, unique step IDs, dependency checks, expression resolution).
- [x] 2.2 Implement sequential step scheduler honoring `dependsOn` and `enabled`.
- [x] 2.3 Implement run-state persistence (`run-state.json`) and run directory layout (`runs/<run-id>/`).

## 3. Implement step execution backends

- [x] 3.1 Implement unified step contract and normalized step result model.
- [x] 3.2 Implement `skill` executor for OpenSpec-oriented steps.
- [x] 3.3 Implement `script` executor interface for deterministic scripted steps.

## 4. Add OpenSpec step type support

- [x] 4.1 Implement step handlers for `openspec.proposal`, `openspec.specs`, and `openspec.design`.
- [x] 4.2 Implement step handlers for `openspec.tasks` and `openspec.apply`.
- [x] 4.3 Add step type whitelist validation and clear error messages for unsupported types.

## 5. Deliver CLI surface and operability

- [x] 5.1 Implement CLI commands: `change new`, `plan init`, `plan validate`, `plan run`, and `plan status`.
- [x] 5.2 Implement resume behavior (`--resume`) and step-level retry/on-fail handling.
- [x] 5.3 Write per-step logs to run directory and expose concise status output for failed runs.

## 6. Verify first increment and document usage

- [x] 6.1 Add integration test for full plan path: `proposal -> specs -> design -> tasks -> apply`.
- [x] 6.2 Add integration test for interruption and resume from failed step.
- [x] 6.3 Document first-increment scope, known limits (no parallel DAG), and next-step extension points.
