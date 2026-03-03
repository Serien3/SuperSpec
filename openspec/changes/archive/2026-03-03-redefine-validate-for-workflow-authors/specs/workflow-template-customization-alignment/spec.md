## MODIFIED Requirements

### Requirement: Unified customization contract across schema and runtime
The system MUST enforce the same workflow template customization contract in `workflow.schema.json` validation and runtime workflow processing, and MUST use this same contract for `superspec validate` workflow-author checks.

#### Scenario: Schema-valid customization is runtime-valid
- **WHEN** a workflow file uses only supported customization fields and passes schema validation
- **THEN** runtime workflow loading and plan generation accept the same customization without additional contract mismatch errors

#### Scenario: Runtime rejection matches schema contract
- **WHEN** a workflow file contains an unsupported customization field path
- **THEN** runtime validation fails
- **AND** the error identifies the unsupported field path and supported field set

#### Scenario: Validate command uses identical contract semantics
- **WHEN** a workflow file is checked with `superspec validate`
- **THEN** accepted and rejected field paths match schema/runtime contract behavior
- **AND** no command-specific field acceptance drift is introduced

### Requirement: Minimal supported customization surface
The system MUST support only an explicitly documented, finite set of customization fields for workflow template data, MUST reject unknown fields, and MUST keep nested customization objects explicitly defined.

#### Scenario: Unknown customization field is rejected
- **WHEN** a workflow includes a customization field outside the supported set
- **THEN** workflow validation fails before plan generation
- **AND** no `plan.json` is written

#### Scenario: Unknown nested customization field is rejected
- **WHEN** a workflow includes an unrecognized nested field within a constrained customization object
- **THEN** validation fails with a nested field path error
- **AND** no partially accepted customization is applied
