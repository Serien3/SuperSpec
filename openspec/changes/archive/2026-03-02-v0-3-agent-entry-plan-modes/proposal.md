## Why

 SuperSpec v1.0.0 defines a pull protocol, but there is no standardized agent guidance that tells an external agent exactly how to run the full `next -> execute -> complete|fail` loop end-to-end. At the same time, plan initialization is effectively fixed to a single template, which blocks the intended workflow of creating a change first and then selecting a plan mode explicitly.

## What Changes

- Add an agent-driven execution guidance artifact (skill and/or AGENT.md) that instructs agents to repeatedly pull the next runnable step, execute it via executor-specific handling, and report completion/failure until terminal state.
- Add plan mode selection to plan initialization so users can explicitly choose an execution pattern (starting with `sdd` mode).
- Clarify and enforce lifecycle boundaries between `change new` and `plan init` so plan creation is explicit and mode-aware.
- Define protocol expectations for agent-executed skill steps, including standardized success/error report payloads.

## Capabilities

### New Capabilities
- `agent-loop-runner-entry`: Defines standardized agent guidance for protocol-driven loop execution.
- `plan-mode-initialization`: Defines mode-based plan generation and mode-specific defaults for new change plans.

### Modified Capabilities
- `change-plan-orchestration`: Update change lifecycle and plan creation requirements to support explicit, mode-aware initialization.
- `agent-driven-plan-execution`: Update payload/report contracts to clearly cover externally executed skill steps in agent loops.

## Impact

- Affected CLI surface: change and plan command flow, including new mode option(s).
- Affected agent guidance: skill/AGENT.md instructions for loop orchestration, executor dispatch boundaries, and completion/failure reporting.
- Affected templates/assets: plan template organization to support mode-specific generation.
- Affected docs/tests: protocol contract docs and integration tests for full loop execution with mixed script/skill steps.
