## MODIFIED Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped execution definition snapshot in `openspec/changes/<change-name>/execution/state.json` as the authoritative execution definition for that change.

#### Scenario: Load execution definition from state snapshot
- **WHEN** a user runs execution for a change
- **THEN** the system loads workflow definition from `execution/state.json`
- **AND** rejects execution if the snapshot file is missing

#### Scenario: Unified advance bootstraps state snapshot for new change
- **WHEN** a user creates a change through `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the system creates a valid `execution/state.json` in that change directory as part of the same command flow
- **AND** the change is immediately executable by protocol pull commands without a separate initialization command

### Requirement: Workflow selection during change creation
The system MUST provide a workflow schema selector for snapshot generation through unified change creation flows.

#### Scenario: Initialize state snapshot with required schema key in unified flow
- **WHEN** a user runs `superspec change advance --new <schema>/<name>` with a supported schema
- **THEN** the system writes a valid generated definition snapshot into `execution/state.json`
- **AND** the resulting snapshot is immediately eligible for execution

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user provides an unsupported workflow schema selector in unified creation flow
- **THEN** initialization fails with a selector validation error
- **AND** no state snapshot file is created or overwritten

### Requirement: Schema-aware workflow resolution
The system MUST resolve initialization content through base-template-plus-workflow composition and persist the resulting definition into the state snapshot.

#### Scenario: Resolve generated snapshot definition from schema key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding workflow and base template inputs
- **AND** writes the resolved definition into `execution/state.json`

### Requirement: Plan schema version validation
The system MUST validate the declared execution definition schema version before any action execution begins.

#### Scenario: Reject unknown schema version
- **WHEN** snapshot definition contains an unsupported `schemaVersion`
- **THEN** the system fails validation
- **AND** does not execute any actions
