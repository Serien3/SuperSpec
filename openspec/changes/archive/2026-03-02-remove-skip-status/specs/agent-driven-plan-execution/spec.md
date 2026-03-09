## MODIFIED Requirements

### Requirement: Next-step retrieval command
The system MUST provide a command to retrieve exactly one executable step for a change in structured JSON form.

#### Scenario: Retrieve next ready step
- **WHEN** a client requests the next step for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** returns only top-level fields `state`, `changeName`, and `step`

#### Scenario: No remaining steps
- **WHEN** all steps are in terminal states according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable step payload

### Requirement: Step failure reporting
The system MUST provide a command for clients to report step failure with structured error payload.

#### Scenario: Fail step with retry policy
- **WHEN** a client reports failure for an step that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the step eligible for retry according to configured backoff

#### Scenario: Fail step without remaining retries
- **WHEN** a client reports failure for an step with no remaining retry attempts
- **THEN** the step transitions to `FAILED`
- **AND** the system applies configured `onFail` behavior without introducing `SKIPPED`

#### Scenario: Propagate dependency failure to downstream steps
- **WHEN** an step reaches terminal `FAILED` and downstream steps depend on it directly or transitively
- **THEN** those downstream steps transition to terminal `FAILED`
- **AND** each propagated failure includes dependency-failure context identifying the upstream failed step

## ADDED Requirements

### Requirement: Two-terminal-state step model
The system MUST represent step terminal outcomes using only `SUCCESS` and `FAILED`.

#### Scenario: Report step status snapshot
- **WHEN** a client requests status during or after execution
- **THEN** each step status is one of `PENDING`, `RUNNING`, `SUCCESS`, or `FAILED`
- **AND** no step is reported as `SKIPPED`

### Requirement: Progress accounting without skipped work
The system MUST compute progress fields without counting skipped outcomes.

#### Scenario: Calculate done and failed counts
- **WHEN** status is computed for a change
- **THEN** `progress.done` counts only steps in `SUCCESS`
- **AND** `progress.failed` counts steps in `FAILED`
