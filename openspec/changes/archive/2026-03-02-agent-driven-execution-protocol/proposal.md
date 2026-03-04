## Why

Prior execution assumed the engine directly ran all actions, but skill-based actions require an Agent runtime boundary that is not reliably represented as a local command. We need a pull-based `v1.0.0` protocol so Agent-driven workflows can execute plans deterministically with clear state transitions.

## What Changes

- Introduce an Agent-driven execution protocol with explicit commands for fetching and reporting action progress.
- Add a pull-style command (`next`) that returns the next runnable action plus structured execution instructions.
- Add report-back commands (`complete` / `fail`) so the engine advances state only from explicit execution results.
- Add lease-based action claiming to avoid duplicate execution by concurrent agents.
- Add execution event/state persistence for auditability and resume.
- Define a structured response contract for `script` and `skill` actions, with optional debug prompt rendering for skills.

## Capabilities

### New Capabilities
- `agent-driven-plan-execution`: Defines pull-based action dispatch, lease management, and result reporting for Agent-orchestrated plan execution.

### Modified Capabilities
- `change-plan-orchestration`: Extend orchestration requirements from direct-run semantics to include command-level execution protocol and lease-safe progression.

## Impact

- Affected areas: SuperSpec CLI surface, orchestration state model, and runtime execution flow between engine and Agent.
- New command surface expected: `next`, `complete`, `fail`, and enhanced `status` semantics.
- Execution now uses protocol commands only (`next`, `complete`, `fail`, `status`) with no legacy direct-run path.
