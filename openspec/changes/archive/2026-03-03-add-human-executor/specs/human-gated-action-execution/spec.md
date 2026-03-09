## ADDED Requirements

### Requirement: Human executor can gate workflow progress
The system SHALL support steps with `executor=human` that pause downstream execution until explicit human outcome is reported.

#### Scenario: Human step becomes running and blocks dependents
- **WHEN** `next` returns an step with `executor=human`
- **THEN** that step transitions to `RUNNING`
- **AND** dependent steps remain non-runnable until the human step is reported complete or failed

### Requirement: Human step payload includes review instructions
The system SHALL return structured human-review metadata in next-step payload for `executor=human` steps.

#### Scenario: Human step payload contract
- **WHEN** the selected runnable step uses `executor=human`
- **THEN** payload includes `stepId`, `executor`, and `prompt`
- **AND** payload includes a `human` object with actionable review instructions

### Requirement: Human review outcome uses existing report commands
The system SHALL use existing completion/failure reporting commands for human step outcomes.

#### Scenario: Human approval reports completion
- **WHEN** a client submits `complete` for a running human step
- **THEN** the step transitions to `SUCCESS`
- **AND** downstream dependencies are refreshed as runnable when satisfied

#### Scenario: Human rejection reports failure
- **WHEN** a client submits `fail` for a running human step
- **THEN** retry and on-fail policy handling follows standard step failure semantics
- **AND** status output reflects failure without introducing new step states
