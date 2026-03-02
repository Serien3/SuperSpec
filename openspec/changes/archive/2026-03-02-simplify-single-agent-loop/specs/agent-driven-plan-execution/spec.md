## MODIFIED Requirements

### Requirement: Next-action retrieval command
The system MUST provide a command to retrieve exactly one executable action for a change in structured JSON form.

#### Scenario: Retrieve next ready action
- **WHEN** a client requests the next action for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** includes action metadata and execution payload for a single runnable action

#### Scenario: No remaining actions
- **WHEN** all actions are completed or skipped according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable action payload

### Requirement: Action completion reporting
The system MUST provide a command for clients to report successful action completion with structured result payload.

#### Scenario: Complete action in single-agent loop
- **WHEN** a client reports completion for the current runnable action
- **THEN** the action state transitions to `SUCCESS`
- **AND** result payload is stored as action output

### Requirement: Action failure reporting
The system MUST provide a command for clients to report action failure with structured error payload.

#### Scenario: Fail action with retry policy
- **WHEN** a client reports failure for an action that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the action eligible for retry according to configured backoff

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script and skill execution modes.

#### Scenario: Script action payload
- **WHEN** the next action uses `executor=script`
- **THEN** the payload includes executable script command details

#### Scenario: Skill action payload
- **WHEN** the next action uses `executor=skill`
- **THEN** the payload includes skill reference (`name`, `version`, `input`, `contextFiles`)
- **AND** does not include full rendered prompt by default

#### Scenario: Skill action completion contract
- **WHEN** a skill action finishes successfully in an external agent runtime
- **THEN** the client reports completion using the returned `actionId`
- **AND** the result payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill action failure contract
- **WHEN** a skill action fails in an external agent runtime
- **THEN** the client reports failure using the returned `actionId`
- **AND** the error payload includes an error code/category and human-readable failure context

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that repeatedly call `next` and report outcomes until terminal state.

#### Scenario: Iterate until done
- **WHEN** an agent repeatedly requests `next` after each completion or failure report
- **THEN** the protocol continues returning runnable actions while work remains
- **AND** eventually returns `done` when the plan reaches terminal state

#### Scenario: Blocked loop behavior
- **WHEN** `next` returns `blocked` due to dependencies or retry backoff
- **THEN** the agent can continue polling without invalidating state
- **AND** serial action ordering remains intact across repeated polling

## REMOVED Requirements

### Requirement: Lease-based action claim safety
**Reason**: Current execution scope is intentionally limited to single-agent single-process serial operation, so lease-based ownership protection is out of scope for now.
**Migration**: Clients should stop sending or expecting lease tokens in `next`/`complete`/`fail` payloads and follow the simplified action-id based serial reporting flow.
