## Purpose

Define schema-driven runtime snapshot initialization behavior for SuperSpec, with extensible workflow resolution.

## Requirements

### Requirement: Schema-driven runtime generation
The system MUST support workflow-based runtime baseline generation when creating a new change through unified entrypoint.

#### Scenario: Initialize runtime snapshot with schema key
- **WHEN** a user runs `superspec change advance --new <schema>/<change-name>`
- **THEN** the system resolves the selected workflow definition and writes a change-scoped `execution/state.json` with runtime step baseline
- **AND** binds `runtime.changeName` to the requested `<change-name>`
- **AND** writes workflow metadata in `state.json.meta` (`schemaVersion`, `workflowId`, `workflowDescription`)

### Requirement: Init-time generated runtime validation
The system MUST validate generated runtime structure during snapshot generation before persisting `execution/state.json`.

#### Scenario: Reject invalid generated runtime during init
- **WHEN** workflow-derived runtime baseline generation produces an invalid execution definition
- **THEN** initialization fails with a validation error
- **AND** `execution/state.json` is not written or modified

### Requirement: Workflow schema selector validation
The system MUST validate requested schema selector values before writing runtime snapshot state.

#### Scenario: Reject unsupported schema selector
- **WHEN** a user requests an unknown schema name through `change advance --new`
- **THEN** initialization fails with a clear validation error
- **AND** does not write or modify `execution/state.json`

### Requirement: Extensible workflow registry
The system MUST resolve runtime generation inputs through an extensible workflow registry so additional workflow strategies can be added without changing command semantics.

#### Scenario: Resolve generation source by supported key
- **WHEN** `change advance --new` is requested for a supported schema key
- **THEN** the system resolves that key to a concrete workflow source
- **AND** applies the same workflow validation rules used for default workflows
