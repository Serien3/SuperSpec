## ADDED Requirements

### Requirement: Unified customization contract across schema and runtime
The system MUST enforce the same workflow template customization contract in `workflow.schema.json` validation and runtime workflow processing.

#### Scenario: Schema-valid customization is runtime-valid
- **WHEN** a workflow file uses only supported customization fields and passes schema validation
- **THEN** runtime workflow loading and plan generation accept the same customization without additional contract mismatch errors

#### Scenario: Runtime rejection matches schema contract
- **WHEN** a workflow file contains an unsupported customization field path
- **THEN** runtime validation fails
- **AND** the error identifies the unsupported field path and supported field set

### Requirement: Minimal supported customization surface
The system MUST support only an explicitly documented, finite set of customization fields for workflow template data, and MUST reject unknown fields.

#### Scenario: Unknown customization field is rejected
- **WHEN** a workflow includes a customization field outside the supported set
- **THEN** workflow validation fails before plan generation
- **AND** no `plan.json` is written

### Requirement: Deterministic customization merge behavior
The system MUST apply supported customization fields using a deterministic precedence order during plan generation.

#### Scenario: Customization conflict resolves deterministically
- **WHEN** the same supported field is defined in base template and workflow customization
- **THEN** generated output follows documented precedence order
- **AND** repeated runs with identical input produce identical `plan.json` values
