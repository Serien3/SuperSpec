## MODIFIED Requirements

### Requirement: Mode-aware plan initialization
The system MUST support scheme-based plan generation when initializing a change plan, while preserving compatibility with mode aliases.

#### Scenario: Initialize SDD-compatible plan through scheme mapping
- **WHEN** a user runs plan initialization with `mode=sdd` or equivalent scheme selection
- **THEN** the system resolves the mapped scheme and writes a change-scoped `plan.json` generated from base template plus scheme content
- **AND** records context values for that change without placeholder leakage

### Requirement: Plan mode validation
The system MUST validate requested mode or scheme values before writing a plan.

#### Scenario: Reject unsupported mode or scheme
- **WHEN** a user requests an unknown mode alias or unknown scheme name
- **THEN** plan initialization fails with a clear validation error
- **AND** does not write or modify `plan.json`

### Requirement: Extensible mode template registry
The system MUST resolve plan generation inputs through an extensible scheme registry so additional plan strategies can be added without changing command semantics.

#### Scenario: Resolve generation source by supported key
- **WHEN** plan initialization is requested for a supported mode alias or scheme key
- **THEN** the system resolves that key to a concrete scheme source plus base template
- **AND** applies the same interpolation and schema validation rules used for default plans
