## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Plan initialization mode selection
The system MUST provide a plan initialization option to select a named plan mode.

#### Scenario: Initialize plan with SDD mode
- **WHEN** a user runs plan initialization with `--mode sdd`
- **THEN** the system writes a valid SDD `plan.json` to the change directory
- **AND** the resulting plan is immediately eligible for plan validation

#### Scenario: Reject unsupported plan mode at init time
- **WHEN** a user runs plan initialization with an unsupported mode name
- **THEN** initialization fails with a mode validation error
- **AND** no plan file is created or overwritten

### Requirement: Mode-aware template resolution
The system MUST resolve plan initialization content through a mode-keyed template registry.

#### Scenario: Resolve default template by mode key
- **WHEN** initialization runs with a supported mode
- **THEN** the engine resolves the corresponding mode template
- **AND** interpolates change-scoped fields before writing the plan
