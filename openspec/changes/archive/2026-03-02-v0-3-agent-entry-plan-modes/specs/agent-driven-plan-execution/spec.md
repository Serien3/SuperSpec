## MODIFIED Requirements

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
- **THEN** the client reports completion using the leased `stepId` and `leaseId`
- **AND** the result payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill step failure contract
- **WHEN** a skill step fails in an external agent runtime
- **THEN** the client reports failure using the leased `stepId` and `leaseId`
- **AND** the error payload includes an error code/category and human-readable failure context

## ADDED Requirements

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that repeatedly call `next` and report outcomes until terminal state.

#### Scenario: Iterate until done
- **WHEN** an agent repeatedly requests `next` after each completion or failure report
- **THEN** the protocol continues returning runnable steps while work remains
- **AND** eventually returns `done` when the plan reaches terminal state

#### Scenario: Blocked loop behavior
- **WHEN** `next` returns `blocked` due to dependencies or retry backoff
- **THEN** the agent can continue polling without invalidating state
- **AND** the protocol preserves lease safety guarantees across repeated polling
