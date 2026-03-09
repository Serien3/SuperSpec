## Why

The current execution protocol lets agents self-recover with retry/backoff logic, but this adds complexity and can hide bad runs behind repeated polling loops. We want deterministic, human-gated recovery: any reported step failure should immediately stop the workflow and escalate to a human.

## What Changes

- Remove retry semantics from runtime behavior and contracts (`defaults.retry`, `step.retry`, retry snapshot mode).
- Change failure handling so any `plan fail` report immediately terminalizes the workflow as `failed`.
- Stop propagating autonomous continuation policies after failure; the protocol always halts and requires human intervention.
- Update CLI/help/skills/docs to remove retry polling guidance and describe fail-fast escalation.
- Mark retry-oriented status surfaces as removed from user-facing contracts.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-driven-plan-execution`: failure reporting semantics become fail-fast and retry-free; status contract drops retry-focused mode.
- `change-plan-orchestration`: runtime configuration surface drops retry policy fields and aligns orchestration behavior to immediate terminal failure on any reported step failure.

## Impact

- Affected code: `src/superspec/engine/protocol.py`, `src/superspec/engine/constants.py`, `src/superspec/engine/validator.py`, `src/superspec/schemas/plan.schema.json`, `src/superspec/cli.py`, `src/superspec/schemas/protocol.contracts.json`.
- Affected tests: integration and CLI tests around retry/status retry mode.
- Affected docs/skills: command docs and loop skills that currently instruct retry polling and retry fields.
- **BREAKING**: `superspec plan status --retry` and retry payload fields are removed; fail now immediately terminalizes workflow.
