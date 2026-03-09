## MODIFIED Requirements

### Requirement: Next-step retrieval command
The system MUST provide a command to retrieve exactly one executable step for a change in structured JSON form.

#### Scenario: Retrieve next ready step
- **WHEN** a client requests the next step for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** includes step metadata and execution payload for a single runnable step

#### Scenario: No remaining steps
- **WHEN** all steps are completed or skipped according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable step payload

### Requirement: Step completion reporting
The system MUST provide a command for clients to report successful step completion with structured result payload.

#### Scenario: Complete step in single-agent loop
- **WHEN** a client reports completion for the current runnable step
- **THEN** the step state transitions to `SUCCESS`
- **AND** result payload is stored as step output

### Requirement: Step failure reporting
The system MUST provide a command for clients to report step failure with structured error payload.

#### Scenario: Fail step with retry policy
- **WHEN** a client reports failure for an step that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the step eligible for retry according to configured backoff

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script and skill execution modes.

#### Scenario: Script step payload
- **WHEN** the next step uses `executor=script`
- **THEN** the payload includes executable script command details

#### Scenario: Skill step payload
- **WHEN** the next step uses `executor=skill`
- **THEN** the payload includes skill reference (`name`, `version`, `input`, `contextFiles`)
- **AND** does not include full rendered prompt by default

#### Scenario: Skill step completion contract
- **WHEN** a skill step finishes successfully in an external agent runtime
- **THEN** the client reports completion using the returned `stepId`
- **AND** the result payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill step failure contract
- **WHEN** a skill step fails in an external agent runtime
- **THEN** the client reports failure using the returned `stepId`
- **AND** the error payload includes an error code/category and human-readable failure context

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that repeatedly call `next` and report outcomes until terminal state.

#### Scenario: Iterate until done
- **WHEN** an agent repeatedly requests `next` after each completion or failure report
- **THEN** the protocol continues returning runnable steps while work remains
- **AND** eventually returns `done` when the plan reaches terminal state

#### Scenario: Blocked loop behavior
- **WHEN** `next` returns `blocked` due to dependencies or retry backoff
- **THEN** the agent can continue polling without invalidating state
- **AND** serial step ordering remains intact across repeated polling

## REMOVED Requirements

### Requirement: Lease-based step claim safety
**Reason**: Current execution scope is intentionally limited to single-agent single-process serial operation, so lease-based ownership protection is out of scope for now.
**Migration**: Clients should stop sending or expecting lease tokens in `next`/`complete`/`fail` payloads and follow the simplified step-id based serial reporting flow.
