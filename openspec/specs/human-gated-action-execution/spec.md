# human-gated-action-execution Specification

## Purpose
Define how `executor=human` actions participate in the protocol-driven plan lifecycle, including payload contract and outcome reporting semantics.
## Requirements
### Requirement: Human executor can gate workflow progress
The system SHALL support actions with `executor=human` that pause downstream execution until explicit human outcome is reported.

#### Scenario: Human action becomes running and blocks dependents
- **WHEN** `next` returns an action with `executor=human`
- **THEN** that action transitions to `RUNNING`
- **AND** dependent actions remain non-runnable until the human action is reported complete or failed

### Requirement: Human action payload includes review instructions
The system SHALL return structured human-review metadata in next-action payload for `executor=human` actions.

#### Scenario: Human action payload contract
- **WHEN** the selected runnable action uses `executor=human`
- **THEN** payload includes `actionId`, `executor`, and `prompt`
- **AND** payload includes a `human` object with actionable review instructions

### Requirement: Human review outcome uses existing report commands
The system SHALL use existing completion/failure reporting commands for human action outcomes.

#### Scenario: Human approval reports completion
- **WHEN** a client submits `complete` for a running human action
- **THEN** the action transitions to `SUCCESS`
- **AND** downstream dependencies are refreshed as runnable when satisfied

#### Scenario: Human rejection reports failure
- **WHEN** a client submits `fail` for a running human action
- **THEN** the workflow follows standard fail-fast semantics and becomes terminal `failed`
- **AND** status output reflects failure without introducing new action states
