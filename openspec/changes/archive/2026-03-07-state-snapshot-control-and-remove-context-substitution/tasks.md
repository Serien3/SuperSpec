## 1. Snapshot-First Runtime Model

- [x] 1.1 Replace `plan.json` loading/orchestration entrypoints with state-snapshot loading helpers.
- [x] 1.2 Implement change bootstrap flow that writes `execution/state.json` (`meta`/`definition`/`runtime`) and creates `execution/events.log` during `change advance --new`.
- [x] 1.3 Ensure protocol initialization and step graph setup read from `state.json.definition` and persist runtime transitions to `state.json.runtime`.

## 2. Remove Runtime Context Substitution

- [x] 2.1 Remove runtime expression resolution module usage from protocol next-step payload generation.
- [x] 2.2 Treat `executor`, `skill`, `script`, `prompt`, `human`, and `inputs` as literal runtime fields and delete `invalid_expression` pathway.
- [x] 2.3 Simplify validation logic by removing expression-scope checks that only served substitution.

## 3. CLI, Tests, And Contract Alignment

- [x] 3.1 Update CLI/workflow generation path and helpers to stop writing or reading `plan.json`.
- [x] 3.2 Update unit/integration tests to assert snapshot bootstrap (`state.json` + `events.log`) and no-compatibility behavior for missing legacy plan files.
- [x] 3.3 Update tests and protocol contract assertions to remove runtime substitution semantics and `invalid_expression` expectations.
