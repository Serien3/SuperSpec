## MODIFIED Requirements

### Requirement: Next-action retrieval command
The system MUST provide a command to retrieve exactly one executable action for a change in structured JSON form.

#### Scenario: Retrieve next ready action
- **WHEN** a client requests the next action for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** returns only top-level fields `state`, `changeName`, and `action`

#### Scenario: No remaining actions
- **WHEN** all actions are in terminal states according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable action payload

### Requirement: Action failure reporting
The system MUST provide a command for clients to report action failure with structured error payload.

#### Scenario: Fail action with retry policy
- **WHEN** a client reports failure for an action that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the action eligible for retry according to configured backoff

#### Scenario: Fail action without remaining retries
- **WHEN** a client reports failure for an action with no remaining retry attempts
- **THEN** the action transitions to `FAILED`
- **AND** the system applies configured `onFail` behavior without introducing `SKIPPED`

#### Scenario: Propagate dependency failure to downstream actions
- **WHEN** an action reaches terminal `FAILED` and downstream actions depend on it directly or transitively
- **THEN** those downstream actions transition to terminal `FAILED`
- **AND** each propagated failure includes dependency-failure context identifying the upstream failed action

## ADDED Requirements

### Requirement: Two-terminal-state action model
The system MUST represent action terminal outcomes using only `SUCCESS` and `FAILED`.

#### Scenario: Report action status snapshot
- **WHEN** a client requests status during or after execution
- **THEN** each action status is one of `PENDING`, `RUNNING`, `SUCCESS`, or `FAILED`
- **AND** no action is reported as `SKIPPED`

### Requirement: Progress accounting without skipped work
The system MUST compute progress fields without counting skipped outcomes.

#### Scenario: Calculate done and failed counts
- **WHEN** status is computed for a change
- **THEN** `progress.done` counts only actions in `SUCCESS`
- **AND** `progress.failed` counts actions in `FAILED`
