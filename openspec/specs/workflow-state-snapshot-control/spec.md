# workflow-state-snapshot-control Specification

## Purpose
Define state snapshot control semantics for workflow execution based on change-scoped runtime files.
## Requirements
### Requirement: State snapshot is the single control file
The system MUST use `superspec/changes/<change-name>/execution/state.json` as the single authoritative control file for workflow execution state.

#### Scenario: State snapshot contains meta and runtime partitions
- **WHEN** a change is created through unified workflow entry
- **THEN** `execution/state.json` includes `meta` and `runtime` top-level sections
- **AND** `meta` contains `schemaVersion`, `workflowId`, and `workflowDescription`
- **AND** `runtime` stores mutable execution lifecycle state

### Requirement: Immutable runtime action baseline
The system MUST freeze workflow-derived action execution fields into `state.json.runtime.actions` at change creation and MUST NOT re-resolve workflow files during protocol execution.

#### Scenario: Workflow file changes after creation do not alter running change
- **WHEN** a workflow source file is modified after a change is created
- **THEN** protocol commands for that change execute using `state.json.runtime.actions`
- **AND** behavior remains deterministic for that change instance

### Requirement: Execution log is created during change bootstrap
The system MUST create `execution/events.log` when a change is created via `change advance --new`.

#### Scenario: Fresh change has both control and log artifacts
- **WHEN** `superspec change advance --new <workflow-type>/<change-name>` succeeds
- **THEN** both `execution/state.json` and `execution/events.log` exist before first action payload is returned
