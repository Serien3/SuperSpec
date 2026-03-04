## Purpose

Define schema-driven plan initialization behavior for SuperSpec, with extensible workflow resolution.

## Requirements

### Requirement: Schema-driven plan initialization
The system MUST support workflow-based plan generation when initializing a change plan.

#### Scenario: Initialize plan with schema key
- **WHEN** a user runs plan initialization with `--schema <name>`
- **THEN** the system resolves the selected workflow definition and writes a change-scoped `plan.json` generated from base template plus workflow content
- **AND** records context values for that change without placeholder leakage

### Requirement: Init-time generated plan validation
The system MUST validate generated plan structure during `plan init` before persisting `plan.json`.

#### Scenario: Reject invalid generated plan during init
- **WHEN** base template plus workflow content produce an invalid plan
- **THEN** plan initialization fails with a validation error
- **AND** `plan.json` is not written or modified

### Requirement: Plan schema selector validation
The system MUST validate requested schema selector values before writing a plan.

#### Scenario: Reject unsupported schema selector
- **WHEN** a user requests an unknown schema name
- **THEN** plan initialization fails with a clear validation error
- **AND** does not write or modify `plan.json`

### Requirement: Extensible workflow registry
The system MUST resolve plan generation inputs through an extensible workflow registry so additional plan strategies can be added without changing command semantics.

#### Scenario: Resolve generation source by supported key
- **WHEN** plan initialization is requested for a supported schema key
- **THEN** the system resolves that key to a concrete workflow source plus base template
- **AND** applies the same interpolation and schema validation rules used for default plans
