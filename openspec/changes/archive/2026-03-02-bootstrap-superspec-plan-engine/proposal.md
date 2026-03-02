## Why

OpenSpec is strong at artifact-level workflows, but SuperSpec needs a higher-level execution layer that can orchestrate a full change lifecycle through an explicit plan. We need this now to make delivery repeatable, resumable, and auditable for SDD-driven Agent workflows.

## What Changes

- Introduce a change-scoped `plan.json` as the authoritative action sequence for a change.
- Define a stable plan schema (`superspec.plan/v0.1`) with action dependencies, execution policy, and variable interpolation.
- Support OpenSpec-like actions inside a plan: `proposal`, `specs`, `design`, `tasks`, and `apply`.
- Define a unified action contract so actions can be executed by either scripts or Agent skills.
- Add run-state and per-action logging requirements to support resume and troubleshooting.

## Capabilities

### New Capabilities
- `change-plan-orchestration`: Defines the change-level plan model, action system, and execution semantics for SuperSpec.

### Modified Capabilities
- None.

## Impact

- Affected areas: OpenSpec change workflow usage, CLI command surface for plan lifecycle, and project documentation.
- New artifacts expected under each change: `plan.json`, `run-state.json`, and run logs.
- Enables future implementation of a lightweight orchestrator without changing existing OpenSpec artifact semantics.
