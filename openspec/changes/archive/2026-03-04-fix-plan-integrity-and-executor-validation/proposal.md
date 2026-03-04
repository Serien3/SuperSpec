## Why

Current protocol execution trusts `plan.context.changeDir` after loading `plan.json` by CLI `change` name, and plan validation accepts arbitrary executor values. This can cause cross-change state writes and contract-breaking action payloads in production.

## What Changes

- Enforce strict binding between CLI target change and `plan.context.changeDir` so execution state can only be read/written under the same change directory.
- Enforce strict executor validation in plan validation to only allow `skill`, `script`, and `human`.
- Require valid string type for explicit `executor` and fail fast with clear validation errors.
- Add regression tests for both protections to prevent future drift.

## Capabilities

### New Capabilities
- `plan-integrity-guardrails`: Enforce runtime integrity checks that prevent plan context from redirecting execution to a different change.

### Modified Capabilities
- `change-plan-orchestration`: Tighten orchestration path resolution to ensure CLI change and plan context target the same change directory.
- `agent-driven-plan-execution`: Tighten action validation so executor type/value cannot violate protocol contract payload expectations.

## Impact

- Affected code:
  - `src/superspec/engine/orchestrator.py`
  - `src/superspec/engine/plan_loader.py`
  - `src/superspec/engine/validator.py`
  - `src/superspec/tests/test_plan_lifecycle.py`
  - `src/superspec/tests/test_integration.py`
- Runtime/API behavior:
  - Malformed plans that previously ran may now fail validation or protocol startup with explicit `ProtocolError`.
- Dependencies/systems:
  - No new external dependencies.
