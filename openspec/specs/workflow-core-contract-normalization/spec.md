## Purpose

Define the minimal workflow core contract and separate execution-critical fields from annotation fields.

## Requirements

### Requirement: Workflow defines explicit core field contract
The workflow template SHALL define a minimal core contract with required top-level fields `workflowId` and `steps`, optional top-level field `version`, and each step SHALL require `id`, `description`, and `executor`.

#### Scenario: Missing core step executor is rejected
- **WHEN** a workflow step omits `executor`
- **THEN** workflow validation fails with an executor-required contract error
- **AND** no runtime snapshot generation output is produced

### Requirement: Step executor payload is mutually exclusive and exact
The system SHALL require exactly one executor payload that matches `steps[].executor`, and SHALL reject any non-matching executor payload fields on the same step.

#### Scenario: Skill executor with extra script payload is rejected
- **WHEN** an step sets `executor: "skill"` and also defines `script`
- **THEN** validation fails for the step payload contract
- **AND** diagnostics identify the invalid mixed executor payload

#### Scenario: Partial human review labels are rejected
- **WHEN** an step sets `executor: "human"` and provides `option` but omits `option.approveLabel` or `option.rejectLabel`
- **THEN** validation fails for the missing human review label field
- **AND** command exits non-zero

### Requirement: Workflow optional fields are explicitly bounded
The workflow template SHALL allow only explicit optional fields: top-level `description`, `finishPolicy`, and `metadata`; and step-level `dependsOn`, `prompt`, plus executor-matching payload fields `skill` or `script` or `option`. When `finishPolicy` is present it SHALL be one of `archive`, `delete`, or `keep`.

#### Scenario: Removed optional step fields are rejected
- **WHEN** an step includes unsupported optional fields outside the bounded set
- **THEN** validation fails with a field-path error
- **AND** unsupported fields are not carried into generated execution definition

#### Scenario: Invalid finish policy is rejected
- **WHEN** a workflow defines `finishPolicy` with a value outside `archive`, `delete`, or `keep`
- **THEN** workflow validation fails with a finish-policy field-path error
- **AND** no runtime snapshot generation output is produced
