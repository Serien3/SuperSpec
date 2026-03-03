# plan-generation-from-scheme Specification

## Purpose
Define how SuperSpec generates change-scoped `plan.json` from a base template plus a selected workflow definition.

## Requirements

### Requirement: Plan rendering from base template and workflow
The system MUST generate change-scoped `plan.json` by combining a generic base plan template with a selected workflow definition, applying only supported workflow customization fields.

#### Scenario: Generate plan with selected workflow
- **WHEN** a user initializes a plan for a change with a valid schema key
- **THEN** the generated `plan.json` contains the base template structural fields
- **AND** includes actions from the selected workflow

#### Scenario: Ignore unsupported customization by failing validation first
- **WHEN** a workflow contains unsupported template customization fields
- **THEN** plan generation is blocked by validation
- **AND** no partially rendered `plan.json` is written

### Requirement: Deterministic merge precedence
The system MUST apply a deterministic merge order across generation inputs for all supported customization fields.

#### Scenario: Resolve conflicting values across sources
- **WHEN** the same field is provided by base template, workflow definition, and init-time overrides
- **THEN** generation applies precedence in a documented deterministic order
- **AND** the resulting value in `plan.json` is predictable and reproducible

### Requirement: Protected change context fields
The system MUST protect change-scoped context values from workflow override.

#### Scenario: Ignore workflow override of change identity
- **WHEN** a workflow attempts to override change-bound context fields such as `changeName` or `changeDir`
- **THEN** generation keeps context values derived from the active change
- **AND** writes a plan bound to the requested change directory
