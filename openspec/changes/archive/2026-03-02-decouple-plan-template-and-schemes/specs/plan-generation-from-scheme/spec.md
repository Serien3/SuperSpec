## ADDED Requirements

### Requirement: Plan rendering from base template and scheme
The system MUST generate change-scoped `plan.json` by combining a generic base plan template with a selected scheme definition.

#### Scenario: Generate plan with selected scheme
- **WHEN** a user initializes a plan for a change with a valid scheme
- **THEN** the generated `plan.json` contains the base template structural fields
- **AND** includes defaults and steps from the selected scheme

### Requirement: Deterministic merge precedence
The system MUST apply a deterministic merge order across generation inputs.

#### Scenario: Resolve conflicting values across sources
- **WHEN** the same field is provided by base template and scheme
- **THEN** generation applies precedence in a documented deterministic order
- **AND** the resulting value in `plan.json` is predictable and reproducible

### Requirement: Protected change context fields
The system MUST protect change-scoped context values from scheme override.

#### Scenario: Ignore scheme override of change identity
- **WHEN** a scheme attempts to override change-bound context fields such as `changeName` or `changeDir`
- **THEN** generation keeps context values derived from the active change
- **AND** writes a plan bound to the requested change directory
