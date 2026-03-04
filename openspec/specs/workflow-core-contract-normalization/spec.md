## Purpose

Define the minimal workflow core contract and separate execution-critical fields from annotation fields.

## Requirements

### Requirement: Workflow defines explicit core field contract
The workflow template SHALL define a minimal core contract with required top-level fields `workflowId`, `version`, and `actions`, and each action SHALL require `id`, `type`, and `executor`.

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

### Requirement: Annotation fields do not alter execution contract
The workflow template MAY include annotation fields for readability and documentation, but these fields SHALL NOT satisfy or override core execution requirements.

#### Scenario: Annotation-only action still fails core contract
- **WHEN** an action includes `title`, `notes`, and `tags` but omits required core executor payload
- **THEN** validation fails on the missing core payload
- **AND** annotation fields are not treated as execution configuration
