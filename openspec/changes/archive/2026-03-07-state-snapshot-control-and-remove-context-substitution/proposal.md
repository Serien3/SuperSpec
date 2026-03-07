## Why

SuperSpec now enforces one workflow binding per change, so maintaining a separate generated `plan.json` adds an unnecessary intermediate artifact and extra complexity. We need a simpler execution model where a change is created once, workflow definition is snapshotted once, and runtime always executes from a single control file.

## What Changes

- Remove change-scoped `plan.json` as a required runtime artifact.
- Initialize `execution/state.json` and `execution/events.log` at change creation time (`change advance --new ...`).
- Redefine `execution/state.json` as the workflow control snapshot plus runtime state:
  - include frozen workflow definition (`definition`)
  - include mutable runtime execution state (`runtime`)
  - include change/workflow metadata (`meta`)
- Update protocol/orchestrator flow to read workflow definition from state snapshot instead of `plan.json`.
- Remove runtime template/context substitution (`${...}`) from action payload resolution.
- Remove expression-scope validation and runtime invalid-expression pathways tied to context substitution.
- **BREAKING**: Existing assumptions that `plan.json` exists and drives protocol execution are removed.
- **BREAKING**: Workflow actions no longer support `${context.*}`, `${variables.*}`, `${actions.*}`, `${state.*}`, `${env.*}` substitutions in runtime fields.

## Capabilities

### New Capabilities
- `workflow-state-snapshot-control`: Define the single-file control model where workflow definition and runtime state are unified in `execution/state.json`.

### Modified Capabilities
- `change-advance-entrypoint`: change creation now initializes execution state/log artifacts immediately and no longer bootstraps `plan.json`.
- `change-plan-orchestration`: orchestration and protocol execution source definition/runtime context from `state.json` snapshot model.
- `agent-driven-plan-execution`: action payload generation uses literal action fields only, without runtime expression substitution.
- `plan-generation-from-scheme`: workflow generation no longer outputs change-scoped `plan.json`; generation target becomes state snapshot definition.

## Impact

- Affected code: `src/superspec/cli.py`, `src/superspec/engine/{workflow_loader.py,plan_loader.py,orchestrator.py,protocol.py,context.py,validator.py,state_store.py}`.
- Affected schemas/assets: `src/superspec/schemas/templates/plan.base.json`, `src/superspec/schemas/plan.schema.json`, workflow generation/validation expectations.
- Affected tests: `tests/test_change_new.py`, `tests/test_plan_lifecycle.py`, `tests/test_integration.py`, plus any tests asserting runtime substitutions.
