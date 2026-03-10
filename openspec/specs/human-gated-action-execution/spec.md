# human-gated-step-execution Specification

## Purpose
Define how `executor=human` steps participate in the protocol-driven plan lifecycle, including payload contract and outcome reporting semantics.
## Requirements
### Requirement: Human executor can gate workflow progress
The system SHALL support steps with `executor=human` that pause downstream execution until explicit human outcome is reported.

#### Scenario: Human step becomes running and blocks dependents
- **WHEN** `next` returns an step with `executor=human`
- **THEN** that step transitions to `RUNNING`
- **AND** dependent steps remain non-runnable until the human step is reported complete or failed

### Requirement: Human step payload may include review instructions
The system SHALL support optional structured human-review metadata in next-step payload for `executor=human` steps.

#### Scenario: Human step payload contract
- **WHEN** the selected runnable step uses `executor=human`
- **THEN** payload includes `stepId`, `executor`, and `prompt`
- **AND** payload includes an `option` object with actionable review instructions only when workflow authors provide `steps[].option`

### Requirement: Human review outcome uses existing report commands
The system SHALL use existing completion/failure reporting commands for human step outcomes.

#### Scenario: Human approval reports completion
- **WHEN** a client submits `complete` for a running human step
- **THEN** the step transitions to `SUCCESS`
- **AND** downstream dependencies are refreshed as runnable when satisfied

#### Scenario: Human rejection reports failure
- **WHEN** a client submits `fail` for a running human step
- **THEN** the workflow follows standard fail-fast semantics and becomes terminal `failed`
- **AND** `superspec change status <change-name>` reflects failure without introducing new step states
