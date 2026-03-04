## MODIFIED Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change, and MUST reject execution when the resolved runtime `context.changeDir` does not match the CLI-requested change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

#### Scenario: Explicit plan initialization lifecycle
- **WHEN** a user creates a change without running plan initialization
- **THEN** the system treats that change as having no executable plan definition yet
- **AND** requires explicit plan initialization before plan validation or protocol execution can proceed

#### Scenario: Reject runtime context directory mismatch
- **WHEN** protocol execution is requested for change `A` but `plan.context.changeDir` resolves to another change directory `B`
- **THEN** protocol startup fails with a structured path validation error
- **AND** no execution state for change `B` is mutated by the command
