## ADDED Requirements

### Requirement: Mode-aware plan initialization
The system MUST support mode-based plan generation when initializing a change plan.

#### Scenario: Initialize SDD mode plan
- **WHEN** a user runs plan initialization with `mode=sdd`
- **THEN** the system writes a change-scoped `plan.json` populated with the SDD step sequence
- **AND** records context values for that change without placeholder leakage

### Requirement: Plan mode validation
The system MUST validate requested plan mode values before writing a plan.

#### Scenario: Reject unsupported mode
- **WHEN** a user requests an unknown plan mode
- **THEN** plan initialization fails with a clear validation error
- **AND** does not write or modify `plan.json`

### Requirement: Extensible mode template registry
The system MUST resolve plan templates through a mode registry so additional modes can be added without changing command semantics.

#### Scenario: Resolve template by mode key
- **WHEN** plan initialization is requested for a supported mode
- **THEN** the system resolves the mode key to a concrete template source
- **AND** applies the same interpolation and schema validation rules used for default plans
