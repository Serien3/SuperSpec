## MODIFIED Requirements

### Requirement: Unified customization contract across schema and runtime
The system MUST enforce one identical workflow authoring contract across `workflow.schema.json` validation, runtime workflow processing, and `superspec validate`, including explicit step executor declaration and exact executor payload matching.

#### Scenario: Schema-valid executor contract is runtime-valid
- **WHEN** a workflow step declares explicit `executor` and provides exactly one matching payload
- **THEN** runtime workflow loading and plan generation accept that step without contract mismatch errors

#### Scenario: Runtime rejection matches schema contract
- **WHEN** a workflow step includes mixed executor payload fields that violate the explicit executor contract
- **THEN** runtime validation fails
- **AND** the error identifies the invalid step field path and expected payload shape

#### Scenario: Validate command uses identical contract semantics
- **WHEN** a workflow file is checked with `superspec validate`
- **THEN** accepted and rejected executor field combinations match schema/runtime contract behavior
- **AND** no command-specific executor acceptance drift is introduced

### Requirement: Minimal supported customization surface
The system MUST support only an explicitly documented, finite workflow customization surface with a core field set and annotation field set, MUST reject unknown fields, and MUST reject workflows that rely on implicit executor inference.

#### Scenario: Unknown customization field is rejected
- **WHEN** a workflow includes a customization field outside the supported set
- **THEN** workflow validation fails before plan generation
- **AND** no `plan.json` is written

#### Scenario: Unknown nested customization field is rejected
- **WHEN** a workflow includes an unrecognized nested field within a constrained customization object
- **THEN** validation fails with a nested field path error
- **AND** no partially accepted customization is applied

#### Scenario: Implicit executor style is rejected
- **WHEN** a workflow step omits `executor` and only defines payload fields such as `skill` or `script`
- **THEN** validation fails for missing explicit executor
- **AND** diagnostics guide the author to set `steps[].executor`
