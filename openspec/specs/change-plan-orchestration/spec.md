## Purpose

Define the change-scoped plan orchestration behavior for SuperSpec v0.3, including plan validation, protocol-driven action execution, and execution state tracking.

## Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

#### Scenario: Explicit plan initialization lifecycle
- **WHEN** a user creates a change without running plan initialization
- **THEN** the system treats that change as having no executable plan definition yet
- **AND** requires explicit plan initialization before plan validation or protocol execution can proceed

### Requirement: Plan initialization schema selection
The system MUST provide a plan initialization option to select a named plan schema/workflow.

#### Scenario: Initialize plan with default schema key
- **WHEN** a user runs plan initialization with `--schema sdd`
- **THEN** the system writes a valid generated `plan.json` to the change directory
- **AND** the resulting plan is immediately eligible for plan validation

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user runs plan initialization with an unsupported schema name
- **THEN** initialization fails with a selector validation error
- **AND** no plan file is created or overwritten

### Requirement: Schema-aware workflow resolution
The system MUST resolve plan initialization content through base-template-plus-workflow composition rather than a single monolithic template file.

#### Scenario: Resolve generated plan content from schema key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding workflow and base template inputs
- **AND** interpolates change-scoped fields before writing the plan

### Requirement: Simplified single-agent starter template
The system MUST provide a default plan template optimized for single-agent, single-process, serial execution.

#### Scenario: Initialize simplified default plan
- **WHEN** a user initializes a plan with the default schema
- **THEN** the generated template expresses a serial action flow suitable for one agent
- **AND** excludes lease-oriented or concurrency-oriented starter fields

### Requirement: Plan schema version validation
The system MUST validate the declared plan schema version before any action execution begins.

#### Scenario: Reject unknown schema version
- **WHEN** `plan.json` contains an unsupported `schemaVersion`
- **THEN** the system fails validation
- **AND** does not execute any actions

### Requirement: Action dependency ordering
The system MUST execute actions in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready actions
- **WHEN** an action has unresolved dependencies
- **THEN** the action is not executed
- **AND** it remains pending until dependencies succeed

#### Scenario: Reject cyclic dependencies
- **WHEN** the action graph contains a cycle
- **THEN** validation fails before execution starts

### Requirement: Unified action execution contract
The system MUST support both `skill` and `script` executors using a shared action contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the execution protocol returns a skill execution payload for an external agent
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the execution protocol returns script command payload for execution
- **AND** stores normalized outputs only after explicit completion reporting

### Requirement: OpenSpec workflow action support
The system MUST support the action types `openspec.proposal`, `openspec.specs`, `openspec.design`, `openspec.tasks`, and `openspec.apply` in plan execution.

#### Scenario: Validate allowed action types
- **WHEN** a plan contains an unsupported action type
- **THEN** plan validation fails with a clear type error

### Requirement: Resumable execution state
The system MUST persist execution state to allow interrupted runs to resume safely in single-agent mode.

#### Scenario: Resume after failed action
- **WHEN** a prior run failed after completing a subset of actions
- **THEN** a resumed agent can continue by fetching the next runnable action via protocol commands
- **AND** previously successful actions are not re-executed unless explicitly requested

### Requirement: Per-action execution logs
The system MUST write per-action execution history for troubleshooting and auditability.

#### Scenario: Inspect action history after failure
- **WHEN** an action fails during execution
- **THEN** a corresponding execution event record exists in protocol execution storage
- **AND** includes error details sufficient for troubleshooting
