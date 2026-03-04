## Purpose

Define the protocol-driven, agent-executed action flow for SuperSpec v0.5.0, including pull-based action retrieval, serial reporting, and executor-specific payload contracts.
## Requirements
### Requirement: Next-action retrieval command
The system MUST provide a command to retrieve exactly one executable action for a change in structured JSON form.

#### Scenario: Retrieve next ready action
- **WHEN** a client requests the next action for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** returns only top-level fields `state`, `changeName`, and `action`

#### Scenario: Next-action expression resolution failure returns protocol error
- **WHEN** the next runnable action contains an unresolved runtime expression
- **THEN** next-action retrieval fails with a structured protocol error payload
- **AND** the error code is `invalid_expression`

#### Scenario: No remaining actions
- **WHEN** all actions are in terminal states according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable action payload

### Requirement: Action completion reporting
The system MUST provide a command for clients to report successful action completion with structured output payload.

#### Scenario: Complete running action
- **WHEN** a client reports completion for a running action
- **THEN** the action state transitions to `SUCCESS`
- **AND** output payload is stored as action output

### Requirement: Action failure reporting
The system MUST provide a command for clients to report action failure with structured error payload.

#### Scenario: Fail action is terminal
- **WHEN** a client reports failure for a running action
- **THEN** the action transitions to `FAILED`
- **AND** the workflow transitions to terminal `failed`
- **AND** no retry scheduling is created

#### Scenario: Propagate dependency failure to downstream actions
- **WHEN** an action reaches terminal `FAILED` and downstream actions depend on it directly or transitively
- **THEN** those downstream actions transition to terminal `FAILED`
- **AND** each propagated failure includes dependency-failure context identifying the upstream failed action

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script, skill, and human execution modes, and MUST reject plans whose explicit `executor` value is not one of `skill`, `script`, or `human`.

#### Scenario: Script action payload
- **WHEN** the next action uses `executor=script`
- **THEN** the payload includes `script_command` and `prompt`

#### Scenario: Skill action payload
- **WHEN** the next action uses `executor=skill`
- **THEN** the payload includes `skillName` and `prompt`
- **AND** does not include context file maps in the action payload

#### Scenario: Human action payload
- **WHEN** the next action uses `executor=human`
- **THEN** the payload includes `human` review metadata and `prompt`
- **AND** does not include `script_command` or `skillName`

#### Scenario: Skill action completion contract
- **WHEN** a skill action finishes successfully in an external agent runtime
- **THEN** the client reports completion using the returned `actionId`
- **AND** the output payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill action failure contract
- **WHEN** a skill action fails in an external agent runtime
- **THEN** the client reports failure using the returned `actionId`
- **AND** the error payload includes an error code/category and human-readable failure context

#### Scenario: Reject invalid explicit executor values at validation time
- **WHEN** a plan action declares an explicit `executor` value outside `skill|script|human`
- **THEN** plan validation fails before protocol execution starts
- **AND** no next-action payload is generated for that invalid action

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that repeatedly call `next` and report outcomes until terminal state.

#### Scenario: Iterate until done
- **WHEN** an agent repeatedly requests `next` after each completion or failure report
- **THEN** the protocol continues returning runnable actions while work remains
- **AND** eventually returns `done` when the plan reaches terminal state

#### Scenario: Blocked loop behavior
- **WHEN** `next` returns `blocked` because no action is currently runnable (for example due to unresolved dependencies or an in-flight `RUNNING` action awaiting report-back)
- **THEN** the agent can continue polling without invalidating state
- **AND** serial action ordering remains intact across repeated polling

### Requirement: Status contract visibility in debug mode
The system MUST return protocol contract metadata in status responses only when debug mode is explicitly requested.

#### Scenario: Status without debug
- **WHEN** a client calls status without debug mode
- **THEN** the response includes execution state and progress fields
- **AND** does not include `contracts`

#### Scenario: Status with debug enabled
- **WHEN** a client calls status with debug mode enabled
- **THEN** the response includes execution state and progress fields
- **AND** includes `contracts` metadata for protocol inspection

### Requirement: Two-terminal-state action model
The system MUST represent action terminal outcomes using only `SUCCESS` and `FAILED`.

#### Scenario: Report action status snapshot
- **WHEN** a client requests status during or after execution
- **THEN** each action status is one of `PENDING`, `READY`, `RUNNING`, `SUCCESS`, or `FAILED`
- **AND** no action is reported as `SKIPPED`

### Requirement: Progress accounting without skipped work
The system MUST compute progress fields without counting skipped outcomes.

#### Scenario: Calculate done and failed counts
- **WHEN** status is computed for a change
- **THEN** `progress.done` counts only actions in `SUCCESS`
- **AND** `progress.failed` counts actions in `FAILED`
