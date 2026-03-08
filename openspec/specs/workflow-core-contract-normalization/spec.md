## Purpose

Define the minimal workflow core contract and separate execution-critical fields from annotation fields.

## Requirements

### Requirement: Workflow defines explicit core field contract
The workflow template SHALL define a minimal core contract with required top-level fields `workflowId`, `version`, and `actions`, and each action SHALL require `id`, `description`, and `executor`.

#### Scenario: Missing core action executor is rejected
- **WHEN** a workflow action omits `executor`
- **THEN** workflow validation fails with an executor-required contract error
- **AND** no plan generation output is produced

### Requirement: Action executor payload is mutually exclusive and exact
The system SHALL require exactly one executor payload that matches `actions[].executor`, and SHALL reject any non-matching executor payload fields on the same action.

#### Scenario: Skill executor with extra script payload is rejected
- **WHEN** an action sets `executor: "skill"` and also defines `script`
- **THEN** validation fails for the action payload contract
- **AND** diagnostics identify the invalid mixed executor payload

#### Scenario: Human executor without instruction is rejected
- **WHEN** an action sets `executor: "human"` and omits `human.instruction`
- **THEN** validation fails for `human.instruction`
- **AND** command exits non-zero

### Requirement: Workflow optional fields are explicitly bounded
The workflow template SHALL allow only explicit optional fields: top-level `description` and `metadata`; and action-level `dependsOn`, `prompt`, plus executor-matching payload fields `skill` or `script` or `human`.

#### Scenario: Removed optional action fields are rejected
- **WHEN** an action includes unsupported optional fields outside the bounded set
- **THEN** validation fails with a field-path error
- **AND** unsupported fields are not carried into generated execution definition
