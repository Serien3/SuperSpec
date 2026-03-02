## MODIFIED Requirements

### Requirement: Plan initialization mode selection
The system MUST provide a plan initialization option to select a named plan scheme, with compatibility support for existing mode names.

#### Scenario: Initialize plan with default SDD compatibility key
- **WHEN** a user runs plan initialization with `--mode sdd` or the equivalent scheme selector
- **THEN** the system writes a valid generated `plan.json` to the change directory
- **AND** the resulting plan is immediately eligible for plan validation

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user runs plan initialization with an unsupported mode alias or scheme name
- **THEN** initialization fails with a selector validation error
- **AND** no plan file is created or overwritten

### Requirement: Mode-aware template resolution
The system MUST resolve plan initialization content through base-template-plus-scheme composition rather than a single monolithic template file.

#### Scenario: Resolve generated plan content from scheme key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding scheme and base template inputs
- **AND** interpolates change-scoped fields before writing the plan
