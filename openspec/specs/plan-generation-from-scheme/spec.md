# plan-generation-from-scheme Specification

## Purpose
Define how SuperSpec generates change-scoped execution `state.json.runtime` step baseline from a selected workflow definition.
## Requirements
### Requirement: Runtime baseline rendering from workflow
The system MUST generate a change-scoped execution runtime baseline from a selected workflow definition, applying only supported workflow customization fields.

#### Scenario: Generate state snapshot runtime baseline with selected workflow
- **WHEN** a user initializes a change with a valid workflow key
- **THEN** the generated `execution/state.json.runtime.steps` contains workflow-derived step execution fields (`id`, `description`, `executor`, dependencies, and executor payload fields)

#### Scenario: Ignore unsupported customization by failing validation first
- **WHEN** a workflow contains unsupported template customization fields
- **THEN** generation is blocked by validation
- **AND** no partially rendered execution snapshot is written

### Requirement: Deterministic generation behavior
The system MUST apply deterministic generation rules for all supported customization fields.

#### Scenario: Resolve conflicting values across sources
- **WHEN** initialization runs repeatedly with identical workflow input
- **THEN** generated runtime step baseline is identical and reproducible

### Requirement: Protected change context fields
The system MUST protect change-scoped identity values from workflow override.

#### Scenario: Keep runtime change identity from CLI selector
- **WHEN** a workflow is selected via `superspec change advance --new <workflow>/<change-name>`
- **THEN** generation keeps `runtime.changeName` equal to `<change-name>`
- **AND** writes a snapshot runtime bound to that requested change
