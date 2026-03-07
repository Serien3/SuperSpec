## MODIFIED Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change, and MUST reject execution when the resolved runtime `context.changeDir` does not match the CLI-requested change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

#### Scenario: Unified advance bootstraps plan for new change
- **WHEN** a user creates a change through `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the system creates a valid `plan.json` in that change directory as part of the same command flow
- **AND** the change is immediately executable by protocol pull commands without a separate initialization command

#### Scenario: Reject runtime context directory mismatch
- **WHEN** protocol execution is requested for change `A` but `plan.context.changeDir` resolves to another change directory `B`
- **THEN** protocol startup fails with a structured path validation error
- **AND** no execution state for change `B` is mutated by the command

### Requirement: Workflow selection during change creation
The system MUST provide a workflow schema selector for plan generation through unified change creation flows.

#### Scenario: Initialize plan with required schema key in unified flow
- **WHEN** a user runs `superspec change advance --new <schema>/<name>` with a supported schema
- **THEN** the system writes a valid generated `plan.json` to the change directory
- **AND** the resulting plan is immediately eligible for plan validation and execution

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user provides an unsupported workflow schema selector in unified creation flow
- **THEN** initialization fails with a selector validation error
- **AND** no plan file is created or overwritten
