## ADDED Requirements

### Requirement: State snapshot is the single control file
The system MUST use `openspec/changes/<change-name>/execution/state.json` as the single authoritative control file for workflow definition and runtime execution state.

#### Scenario: State snapshot contains definition and runtime partitions
- **WHEN** a change is created through unified workflow entry
- **THEN** `execution/state.json` includes `meta`, `definition`, and `runtime` top-level sections
- **AND** `definition` stores frozen workflow content for that change
- **AND** `runtime` stores mutable execution lifecycle state

### Requirement: Immutable workflow definition snapshot
The system MUST freeze workflow definition into `state.json` at change creation and MUST NOT re-resolve workflow files during protocol execution.

#### Scenario: Workflow file changes after creation do not alter running change
- **WHEN** a workflow source file is modified after a change is created
- **THEN** protocol commands for that change execute using `state.json.definition`
- **AND** behavior remains deterministic for that change instance

### Requirement: Execution log is created during change bootstrap
The system MUST create `execution/events.log` when a change is created via `change advance --new`.

#### Scenario: Fresh change has both control and log artifacts
- **WHEN** `superspec change advance --new <workflow-type>/<change-name>` succeeds
- **THEN** both `execution/state.json` and `execution/events.log` exist before first step payload is returned
