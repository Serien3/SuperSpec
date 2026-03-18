## MODIFIED Requirements

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
