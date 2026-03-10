## Purpose

Define the protocol-driven, agent-executed step flow for SuperSpec v1.1.0, including pull-based step retrieval, serial reporting, and executor-specific payload contracts.
## Requirements
### Requirement: Next-step retrieval command
The system MUST provide a command to retrieve exactly one executable step for a change in structured JSON form.

#### Scenario: Retrieve next ready step
- **WHEN** a client requests the next step for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** returns only top-level fields `state` and `step`

#### Scenario: No remaining steps
- **WHEN** all steps are in terminal states according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable step payload

### Requirement: Step completion reporting
The system MUST provide a command for clients to report successful step completion.

#### Scenario: Complete running step
- **WHEN** a client reports completion for a running step
- **THEN** the step state transitions to `SUCCESS`
- **AND** the step is marked finished without persisting an step output payload

### Requirement: Step failure reporting
The system MUST provide a command for clients to report step failure.

#### Scenario: Fail step is terminal
- **WHEN** a client reports failure for a running step
- **THEN** the step transitions to `FAILED`
- **AND** the workflow transitions to terminal `failed`
- **AND** all remaining non-terminal steps are terminalized according to fail-fast policy
- **AND** no retry scheduling is created

#### Scenario: Propagate dependency failure to downstream steps
- **WHEN** an step reaches terminal `FAILED` and downstream steps depend on it directly or transitively
- **THEN** those downstream steps transition to terminal `FAILED`
- **AND** dependency-failure context is recorded in execution events

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script, skill, and human execution modes, and MUST reject plans whose explicit `executor` value is not one of `skill`, `script`, or `human`.

#### Scenario: Script step payload
- **WHEN** the next step uses `executor=script`
- **THEN** the payload includes `script_command` and `prompt`

#### Scenario: Skill step payload
- **WHEN** the next step uses `executor=skill`
- **THEN** the payload includes `skillName` and `prompt`
- **AND** does not include context file maps in the step payload

#### Scenario: Human step payload
- **WHEN** the next step uses `executor=human`
- **THEN** the payload includes `prompt`
- **AND** may include `option` review metadata when configured on the step
- **AND** does not include `script_command` or `skillName`

#### Scenario: Runtime fields are not expression-expanded
- **WHEN** step runtime fields contain `${...}` substrings
- **THEN** protocol payload generation treats those fields as literal string content
- **AND** no runtime expression expansion scope is applied

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that repeatedly call `next` and report outcomes until terminal state.

#### Scenario: Iterate until done
- **WHEN** an agent repeatedly requests `next` after each completion or failure report
- **THEN** the protocol continues returning runnable steps while work remains
- **AND** eventually returns `done` when the plan reaches terminal state

#### Scenario: Blocked loop behavior
- **WHEN** `next` returns `blocked` because no step is currently runnable due to unresolved dependencies and no in-flight `RUNNING` step is available for resume
- **THEN** the agent can continue polling without invalidating state
- **AND** serial step ordering remains intact across repeated polling

#### Scenario: Return in-flight running step for session handoff
- **WHEN** a change has an in-flight `RUNNING` step and a client requests `next`
- **THEN** the protocol returns state `ready` with that same in-flight step payload
- **AND** does not allocate a new step until the in-flight step is reported complete or failed

### Requirement: Status contract visibility in debug mode
The system MUST return protocol contract metadata in status responses only when debug mode is explicitly requested.

#### Scenario: Status without debug
- **WHEN** a client calls `superspec change status <change-name>` without debug mode
- **THEN** the response includes execution state and progress fields
- **AND** does not include `contracts`

#### Scenario: Status with debug enabled
- **WHEN** a client calls `superspec change status <change-name>` with debug mode enabled
- **THEN** the response includes execution state and progress fields
- **AND** includes `contracts` metadata for protocol inspection

### Requirement: Two-terminal-state step model
The system MUST represent step terminal outcomes using only `SUCCESS` and `FAILED`.

#### Scenario: Report step status snapshot
- **WHEN** a client requests `superspec change status <change-name>` during or after execution
- **THEN** each step status is one of `PENDING`, `READY`, `RUNNING`, `SUCCESS`, or `FAILED`
- **AND** no step is reported as `SKIPPED`

### Requirement: Progress accounting without skipped work
The system MUST compute progress fields without counting skipped outcomes.

#### Scenario: Calculate done and failed counts
- **WHEN** `superspec change status <change-name>` is computed for a change
- **THEN** `progress.done` counts only steps in `SUCCESS`
- **AND** `progress.failed` counts steps in `FAILED`

#### Scenario: Terminal failed workflow has no remaining work
- **WHEN** `superspec change status <change-name>` is computed after a fail-fast terminal failure
- **THEN** `progress.remaining` is `0`
- **AND** no step remains in `PENDING`, `READY`, or `RUNNING`
