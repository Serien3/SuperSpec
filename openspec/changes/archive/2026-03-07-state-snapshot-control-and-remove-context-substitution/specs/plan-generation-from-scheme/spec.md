## MODIFIED Requirements

### Requirement: Plan rendering from base template and workflow
The system MUST generate a change-scoped execution definition snapshot by combining a generic base template with a selected workflow definition, applying only supported workflow customization fields.

#### Scenario: Generate state snapshot definition with selected workflow
- **WHEN** a user initializes a change with a valid schema key
- **THEN** the generated `execution/state.json.definition` contains base template structural fields
- **AND** includes actions from the selected workflow

#### Scenario: Ignore unsupported customization by failing validation first
- **WHEN** a workflow contains unsupported template customization fields
- **THEN** generation is blocked by validation
- **AND** no partially rendered execution snapshot is written

### Requirement: Deterministic merge precedence
The system MUST apply a deterministic merge order across generation inputs for all supported customization fields.

#### Scenario: Resolve conflicting values across sources
- **WHEN** the same field is provided by base template and workflow definition
- **THEN** generation applies precedence in a documented deterministic order
- **AND** the resulting value in snapshot definition is predictable and reproducible

### Requirement: Protected change context fields
The system MUST protect change-scoped context values from workflow override.

#### Scenario: Ignore workflow override of change identity
- **WHEN** a workflow attempts to override change-bound context fields such as `changeName` or `changeDir`
- **THEN** generation keeps context values derived from the active change
- **AND** writes a snapshot definition bound to the requested change directory
