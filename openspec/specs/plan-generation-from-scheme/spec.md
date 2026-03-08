# plan-generation-from-scheme Specification

## Purpose
Define how SuperSpec generates change-scoped execution `state.json.runtime` action baseline from a selected workflow definition.
## Requirements
### Requirement: Runtime baseline rendering from workflow
The system MUST generate a change-scoped execution runtime baseline from a selected workflow definition, applying only supported workflow customization fields.

#### Scenario: Generate state snapshot runtime baseline with selected workflow
- **WHEN** a user initializes a change with a valid schema key
- **THEN** the generated `execution/state.json.runtime.actions` contains workflow-derived action execution fields

#### Scenario: Ignore unsupported customization by failing validation first
- **WHEN** a workflow contains unsupported template customization fields
- **THEN** generation is blocked by validation
- **AND** no partially rendered execution snapshot is written

### Requirement: Deterministic generation behavior
The system MUST apply deterministic generation rules for all supported customization fields.

#### Scenario: Resolve conflicting values across sources
- **WHEN** initialization runs repeatedly with identical workflow input
- **THEN** generated runtime action baseline is identical and reproducible

### Requirement: Protected change context fields
The system MUST protect change-scoped context values from workflow override.

#### Scenario: Ignore workflow override of change identity
- **WHEN** a workflow attempts to override change-bound context fields such as `changeName` or `changeDir`
- **THEN** generation keeps context values derived from the active change
- **AND** writes a snapshot runtime bound to the requested change directory
