# workflow-validation-command Specification

## Purpose
Define the human-facing workflow validation command contract so workflow authors can validate templates before plan generation.

## Requirements

### Requirement: Validate command targets workflow templates
The `superspec validate` command MUST validate workflow template documents intended for plan generation, and MUST NOT require a change-scoped `plan.json` input.

#### Scenario: Validate local workflow by schema name
- **WHEN** a user runs `superspec validate --schema custom-flow`
- **THEN** the command resolves `custom-flow.workflow.json` from supported workflow locations
- **AND** validates that workflow document against workflow validation contract

#### Scenario: Validate explicit workflow file path
- **WHEN** a user runs `superspec validate --file /path/to/custom.workflow.json`
- **THEN** the command validates the workflow at that exact path
- **AND** does not require a change name

### Requirement: Validate command enforces generation readiness
The `superspec validate` command MUST perform generation-readiness checks in addition to structural schema checks so a passing workflow is usable for subsequent `plan init` generation.

#### Scenario: Reject semantically invalid dependency graph
- **WHEN** a workflow document has an action dependency that references a missing action id
- **THEN** validation fails with an error for the dependency path
- **AND** command exits non-zero

#### Scenario: Accept workflow that is generation-ready
- **WHEN** a workflow passes structure, semantic, and generation-readiness checks
- **THEN** validation succeeds
- **AND** command exits zero

### Requirement: Validate command returns actionable diagnostics
The command MUST provide actionable diagnostics for authoring failures in both human-readable and machine-readable forms.

#### Scenario: Human-readable validation failure
- **WHEN** workflow validation fails in default output mode
- **THEN** output includes error code, field path, and a concise fix-oriented message

#### Scenario: JSON validation failure payload
- **WHEN** workflow validation fails and user passes `--json`
- **THEN** output includes a stable `errors` array with `code`, `path`, `message`, and `hint` fields
- **AND** command exits non-zero
