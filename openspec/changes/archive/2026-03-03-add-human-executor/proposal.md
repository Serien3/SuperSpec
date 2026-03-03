## Why

Current workflows support `skill` and `script` executors only. Teams need a first-class way to pause between automated actions for human review and then resume execution only after explicit human feedback.

## What Changes

- Add a new action executor type: `human`.
- Extend `plan next` action payload generation to emit human-review instructions for `human` actions.
- Keep protocol flow unchanged (`next -> complete|fail`): human approval is reported via `complete`, rejection via `fail`.
- Extend workflow/plan validation to accept `human` executor payload and reject malformed human actions.
- Update protocol contracts and agent-loop execution guidance to include `human` dispatch handling.

## Capabilities

### New Capabilities
- `human-gated-action-execution`: Introduce human-gated action execution in workflow protocol with explicit review instructions and resume semantics.

### Modified Capabilities
- `agent-driven-plan-execution`: Expand executor model and action payload contracts from `skill|script` to `skill|script|human`.

## Impact

- Affected code:
  - `src/superspec/engine/protocol.py`
  - `src/superspec/engine/validator.py`
  - `src/superspec/schemas/workflow.schema.json`
  - `src/superspec/schemas/protocol.contracts.json`
  - `src/superspec/skills/superspec-agent-driven-loop/SKILL.md`
  - related tests under `src/superspec/tests/`
- No new protocol commands required; compatibility impact is additive.
- Existing workflows remain valid and behavior-preserving.
